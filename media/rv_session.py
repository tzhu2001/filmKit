import os, sys, time, traceback, socket
import subprocess

import media.config
from media.config import RV_ROOT, RV_CONNECT_TIME_OUT, PLAY_PREVIEW, PLAY_LEFT_EYE_ONLY, MOVIE_FORMATS

from tweak.network              import rvNetwork

from media                      import resource


# check if rvls is available
HAS_RVLS = None
def has_rv():
    if not HAS_RVLS:
        os.chdir(os.path.normpath(RV_ROOT()))
        stdout, stderr = subprocess.call('"%s" -l' % os.path.join(RV_ROOT(), "rvls"), 
                                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        
        HAS_RVLS = False if stderr else True

    return HAS_RVLS

RV_SESSION              = {}
LAST_ACCESSED_RV_KEY    = None  

# this is a hack to deal with compare mode crashing
COMPARE_MODE = False 

def conn(session_key=None):
    global RV_SESSION
    global _thread_do_not_exit_until_all_rv_session_closed
    
    if session_key==None: session_key = "default"
    
    if session_key not in RV_SESSION.keys():
        RV_SESSION[session_key] = RvSession(key = session_key)
        
    return RV_SESSION[session_key]


def disconnect_all():
    global RV_SESSION
    
    for rvs in RV_SESSION.values():
        print "disconnecting to rv..."
        try:
            rvs.eval("close()")
            rvs.rvc.disconnect()
        except:
            pass

def get_next_free_port(host):
    ''' the next free socket port '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    
    print "obtain free port %s" % port
    
    return port


import re
class RvSession :
    def __init__ (self, host="localhost", port_num=40005, key=None):
        
        self.MOVIE_FORMATS = ["mov", "avi", "mpg"]
        self.IMAGE_FORMATS = ["exr", "jpg", "jpeg", "png", "bmp", "tif", "tiff"]        
        
        self.rvc = None
        self.host = host
        self.port_num = port_num
        
        self._rv_source_list = {}
        self._rv_proc = None
        
        self._out_of_range_info_image = None
        
        self._state_hold_on_missing_frames = True
        
        self._session_key = key
        

    def _rv_playhelper_add_clip_sources(self, clip, skip_audio_lookup=False):
        """
        Add a clip to the rv session, either movie or frames depending on the config.play_preference
        Returns the RV node id, and also what play_type was used.
        
        skip_audio_lookup option is provide to speed up dynamic loading latest audio file.
        """
        ################################
        # Get the video source
        ################################
        
        # the last one is the latest edition
        frame_in, frame_out = clip.play_range()        
        
        # format the source path to something more receptive by rv
        all_source = clip.source_path(  flg_stereo  = True, 
                                        flg_preview = PLAY_PREVIEW )        
        
        if PLAY_LEFT_EYE_ONLY:
            all_source = all_source[:1] 
        
        all_source = [ media.format_img_seq_pattern(s, "-@",  frame_in=frame_in, frame_out=frame_out ) for s in all_source ] 
        all_source = [ s.replace("\\","/") for s in all_source ]
        
        rv_source_id = self._rv_add_source(all_source[0]) 
        
        ################################
        # Get the audio source        
        ################################        
        # set the audio offset if it's frames
        if not skip_audio_lookup and all_source[0].split(".")[-1] not in MOVIE_FORMATS:
            # set the media, all sources, both left and right eye for stereo as well as the audio
            if hasattr(clip, "get_published_audio"):
                audio_path, audio_offset = clip.get_published_audio()
            else:
                audio_path, audio_offset = clip.get_audio()
              
            audio_offset = float(audio_offset - frame_in)
            audio_offset = audio_offset / clip.get_fps() 
             
            if  audio_path:            
                all_source.append(audio_path)
            
            self.eval('setFloatProperty("%(rv_source_id)s_source.group.audioOffset", float[]{%(audio_offset)s} )' % vars())

        ################################
        # push sources to rv session
        ################################ 
        # sorces convert to rv string
        assert( type(all_source)==list )        
        all_source_str = ",".join ([ '"%s"' % s for s in all_source ])
        
        
        print "all source to be loaded to RV:", "\n".join(all_source)
        
        self.eval('setSourceMedia("%s_source", string[]{%s})' % (rv_source_id, all_source_str))
        
        # toggle sRGB convert for tif and exr sources 
        # TODO: make this work with the latest RV 
#         if all_source and all_source[0].split(".")[-1] in ("tif", "exr", "tiff"):            
#             self.eval('setIntProperty("%(rv_source_id)s_color.color.sRGB2linear", int[] {0});' % vars() )
#             self.eval('setIntProperty("%(rv_source_id)s_color.color.Rec709ToLinear", int[] {0});' % vars() )
#         else:
#             self.eval('setIntProperty("%(rv_source_id)s_color.color.sRGB2linear", int[] {0});' % vars() )
#             self.eval('setIntProperty("%(rv_source_id)s_color.color.Rec709ToLinear", int[] {1});' % vars() )
        
        self._rv_source_list[ rv_source_id ] = clip
         
        return rv_source_id
    
    
    
    def _rv_get_no_source_node(self, duration):
        retime_node = self.eval('newNode("RVRetimeGroup","retime_no_source")').strip('"')
        self.eval( 'setNodeInputs("%s", string[]{"%s"})' % (retime_node, self._no_source_image) )
        self.eval( 'setFloatProperty("%s_retime.visual.scale", float[]{%s})' % (retime_node, duration) )
        
        return retime_node
    
    
    def _rv_get_out_of_range_node(self, duration, hold_index=None, hold_clip=None):
        # first check if in the pool there are already some floating retime nodes
        # if not, create more
        retime_node = self.eval('newNode("RVRetimeGroup","retime_out_of_range")').strip('"')
        
        # specify the source for the missing frames
        if self._state_hold_on_missing_frames and hold_index!=None: # use the head/tail            
            hold_source_node = self._rv_playhelper_add_clip_sources(hold_clip)
            
            if hold_clip.movie_frame_offset > 0 and hold_clip.source_type(media.config.PLAY_PREVIEW)=="movie":
                movie_offset = hold_clip.movie_frame_offset
                self.eval('setIntProperty("%(hold_source_node)s_source.group.rangeOffset", int[]{%(movie_offset)s})' % vars())
                hold_index     += hold_clip.movie_frame_offset
                            
            self.eval('setIntProperty("%(hold_source_node)s_source.cut.in", int[]{%(hold_index)s})' % vars())
            self.eval('setIntProperty("%(hold_source_node)s_source.cut.out", int[]{%(hold_index)s})' % vars())
            self.eval('setNodeInputs("%s", string[]{"%s"})' % (retime_node, hold_source_node))
            
            self._rv_add_clip_meta_data(hold_source_node, self._clean_meta(hold_clip.get_meta()) )
            
        else: # use out of range image
            self.eval('setNodeInputs("%s", string[]{"%s"})' % (retime_node, self._out_of_range_info_image))        
        
        self.eval('setFloatProperty("%s_retime.visual.scale", float[]{%s})' % (retime_node, duration))
        
        return retime_node    
    
    
    def _clean_meta(self, meta):
        '''
        @param meta ensure the meta data doesn't contain any funny characters 
        '''
        cleaned_hash = {}
        for key in meta.keys():
            value = meta[key]
            if value==None:
                value = ""
            else:
                value = str(value)
                
            value = value.replace('"', "'").replace('\\', '/').replace('\n', ' ').replace("<", " ").replace(">", " ")
            
            result = re.search("[\w/\s]*", value)
            if result:
                cleaned_hash[key] = result.group()
        
        return cleaned_hash
    
            
    def _rv_clear_session(self):
        #self.eval('addSource("%s")' %  os.path.join( resource.get_root_path(), "dummy.wav").replace('\\','/')) # this hack turns enables the audio for the rest of the session
        self.eval("clearSession()")
        self.eval('rvui.setStereo("off")')
        self._loading_info_image = self._rv_add_source( resource.get("loading.png") )                
        self._out_of_range_info_image = self._rv_add_source(os.path.join(resource.get_root_path(), "source_out_of_range.png").replace('\\', '/')) 
        self._no_source_image = self._rv_add_source(os.path.join(resource.get_root_path(), "no_source.png").replace('\\', '/'))
        
        
    def _rv_new_sequence(self, seq_name="seq"):
        seq_node = self.eval('newNode("RVSequenceGroup", "%s")' % seq_name).strip('"')
#        self.eval('setIntProperty("%s.timing.retimeInputs", int[]{%s})' % (seq_node, 0))
        
        return seq_node
        

    def _rv_new_stack(self, stack_name="stack"):
        stack_node = self.eval('newNode("RVStackGroup", "%s")' % stack_name).strip('"')
        self.eval('setIntProperty("%s.timing.retimeInputs", int[]{%s})' % (stack_node, 0))
        
        return stack_node
    

    def _rv_new_layout(self, stack_name="layout"):
        layout_node = self.eval('newNode("RVLayoutGroup", "%s")' % stack_name).strip('"')
        self.eval('setIntProperty("%s.timing.retimeInputs", int[]{%s})' % (layout_node, 0))
        
        return layout_node

    
    def _rv_add_clip(self, seq_node, clip, single_frame_position=None):
        """
        Load the source to RV
        @param clip
        @type clip: clipStore.clip_source.ClipSource 
        """
        
        if clip.source_path(flg_preview=media.config.PLAY_PREVIEW)==None: # use in compare modes            
            play_range = clip.play_range()
            no_source_node = self._rv_get_no_source_node( play_range[1] - play_range[0] + 1 )  
            # self._rv_add_clip_meta_data(no_source_node, clip.get_meta()) # can not add meta data to a retime node 
            return [ no_source_node ]
        
        
        elif single_frame_position:
            # only play one frame            
            rv_source_node =  self._rv_playhelper_add_clip_sources(clip, skip_audio_lookup=True)
            
            _in, _out   = clip.get_frames_range()
            p_in, p_out = clip.get_play_range()
            _in         = max(_in, p_in)
            _out        = min(_out, p_out)
            
            if single_frame_position=="first":
                _index = _in
            elif single_frame_position=="last":
                _index = _out
            else:
                _index = int ( (_in + _out) / 2 )
                            
            
            if clip.movie_frame_offset>0 and clip.source_type(media.config.PLAY_PREVIEW)=="movie": 
                # if it's movie do offset so RV correctly display the frame index
                movie_offset = clip.movie_start_index()

                self.eval('setIntProperty("%(rv_source_node)s_source.group.rangeOffset", int[]{%(movie_offset)s})' % vars())
                                
            self.eval('setIntProperty("%(rv_source_node)s_source.cut.in", int[]{%(_index)s})' % vars())
            self.eval('setIntProperty("%(rv_source_node)s_source.cut.out", int[]{%(_index)s})' % vars())
                    
            return [ rv_source_node ]
        
            
        else:            
            rv_source_node =  self._rv_playhelper_add_clip_sources(clip)
            
            # cache the clip data            
            head_padding, play_in, play_out, tail_padding = clip.get_play_data(flg_preview=media.config.PLAY_PREVIEW)            
            rv_clip_node_list = []        
                
            # add the header pad clip (if any)
            if head_padding != None and head_padding > 0:
                pad_node = self._rv_get_out_of_range_node(head_padding, hold_index=play_in, hold_clip=clip)
                rv_clip_node_list.append(pad_node)                    
            
            # add the source clip
            if play_in != None:
                if clip._movie_start_index>0 and \
                        clip.source_type(media.config.PLAY_PREVIEW)=="movie": 
                    # if it's movie do offset so RV correctly display the frame index
                    movie_offset = clip._movie_start_index - 1
                    
                    if not COMPARE_MODE:
                        self.eval('setIntProperty("%(rv_source_node)s_source.group.rangeOffset", int[]{%(movie_offset)s})' % vars())
                        play_in     += clip._movie_start_index
                        play_out    += clip._movie_start_index                    
                
                self.eval('setIntProperty("%(rv_source_node)s_source.cut.in", int[]{%(play_in)s})' % vars())
                self.eval('setIntProperty("%(rv_source_node)s_source.cut.out", int[]{%(play_out)s})' % vars())
                
                if hasattr(clip, 'load_source_info'):
                    clip.load_source_info()
                                    
                self._rv_add_clip_meta_data(rv_source_node, self._clean_meta(clip.get_meta()) )                
                    
                rv_clip_node_list.append(rv_source_node)
                
    
            # add the tail pad clip (if any)
            if tail_padding != None and tail_padding > 0:
                pad_node = self._rv_get_out_of_range_node(tail_padding, hold_index=play_out, hold_clip=clip)
                rv_clip_node_list.append(pad_node)
                  
            return rv_clip_node_list

   
    def _rv_add_clip_meta_data(self, source_node, all_meta):
        meta_key = all_meta.keys()
        
        display_key_list = set(meta_key).difference( set(media.config.PLAY_ANNONTATE_META_HIDDEN_LIST) )
        display_key_list = list(display_key_list)
        
        display_key_list.sort( lambda x,y: cmp(media.config.PLAY_ANNONTATE_META_KEY_LABEL[x] if media.config.PLAY_ANNONTATE_META_KEY_LABEL.has_key(x) else x.upper(), 
                                               media.config.PLAY_ANNONTATE_META_KEY_LABEL[y] if media.config.PLAY_ANNONTATE_META_KEY_LABEL.has_key(y) else y.upper())  )
        
        display_key_list.reverse()
        
        meta_str_list = [] 
        for key in display_key_list:
            if key in all_meta and key.strip()!="":                
                key_label     = media.config.PLAY_ANNONTATE_META_KEY_LABEL[key] if key in media.config.PLAY_ANNONTATE_META_KEY_LABEL else key
                key_label     = key_label.replace("\\", "/")
                key_label     = " ".join( [ k[0].upper() + k[1:] for k in key_label.split("_") ] )
                
                value   = all_meta[key] if all_meta[key] != "" else " "
                value   = str(value).replace("\\", "/")

                # --- extra double-quotes in the Snapshot value throw errors, replace them with singles...  
                if key_label == 'Snapshot':
                    value = value.replace('"',"'")

                meta_str_list.append('"%s=%s"' % (key_label, value))
        
        meta_str = ",".join(meta_str_list)
                    
        self.eval('newProperty("%(source_node)s_source.site_annotation.metadata", commands.StringType, 1)' % vars())
        self.eval('insertStringProperty("%(source_node)s_source.site_annotation.metadata", string[]{%(meta_str)s})' % vars())
        
    
    def start(self):
        self.play([])
        

    def play(self, playable, compare_mode=None, single_frame_position=None):
        global COMPARE_MODE 
        COMPARE_MODE = compare_mode
        
        print 'RV_SUPPORT_PATH:', os.environ.get("RV_SUPPORT_PATH") #"Z:/tools/production/rv_toonbox/RV_SUPPORT_DEV")
        print 'MU_MODULE_PATH:', os.environ.get("MU_MODULE_PATH") #, "Z:/tools/production/rv_toonbox/RV_SUPPORT_DEV/Mu" )
    
        try:            
            self._play_raw(playable, compare_mode=compare_mode, single_frame_position=single_frame_position)
            
            if compare_mode!="contact_sheet":
                self.eval("play()")
            
        except:
            print "Failed to play everything...."            
            traceback.print_exc()
            
            
    def _add_sequence(self, playable, single_frame_position=None):
        """
        Iterate through the list of playable (paths to movies/frames)
        and add it to a sequence RV node.
        Returns the list of RV sources nodes that contains the playables.
        
        If single frame position is chosen and frames are 
        """
        if hasattr(playable, 'list_clip'):
            clip_list = playable.list_clip()
            
        elif type(playable) not in (list, tuple):
            clip_list = [ playable ]
                  
        else:
            clip_list = playable
        
        seq_node = self._rv_new_sequence()
        
        rv_clip_node_list = []
        
        frame_count = 0
        mark_frame_list = []
        has_stereo_source = False
        
        # add the source clips
        for clip in clip_list:
            # TODO: to use set media to add the stereo source as well as audio. 
            # TODO: set audio offset
            # TODO: use sequence to group together the clips
            source_path = clip.source_path(     flg_stereo = True,
                                                flg_preview = PLAY_PREVIEW )
            
            if source_path==None: 
                continue
            
            _new_clip_node_list = self._rv_add_clip(seq_node, clip, single_frame_position=single_frame_position)
            _playin, _playout = clip.play_range()
            
            mark_frame_list.append(frame_count)             # keep the timeline spot  
            frame_count += (_playout - _playin + 1)                
            
            rv_clip_node_list.extend(_new_clip_node_list)   # keep the list of  nodes to append to rv sequence node
            
            # determine if there has been a stereo source
            if len( source_path ) > 1:
                has_stereo_source = True                
        
             
        # add all the clips to an rv sequence     
        node_list_string = ",".join(['"%s"' % n for n in rv_clip_node_list ])    
    
        self.eval('setNodeInputs("%(seq_node)s", string[]{%(node_list_string)s})' % vars())        
        
        
        return {
                'seq_node': seq_node,
                'clip_node_list': rv_clip_node_list,
                'mark_frame_list': mark_frame_list,
                'has_stereo_source': has_stereo_source
                }
        
        
    def _play_raw(self, playable, compare_mode=None, single_frame_position="middle"):     
        """
        playable is either a Playlist or a list of Clips
        if launch in contact sheet mode can pick the frame to use        
        """   
        # TODO: later on we should be more frugal with clearing, ie: reuse session clips and only modify play range etc.
        if not self.is_rv_connected():
            self.new_session()
        
        self._rv_clear_session()
        
        result = None
        if compare_mode==None:  # play in sequence mode
            result = self._add_sequence(playable)
            self.eval('setViewNode("%s")' % result['seq_node'])
            
            # set stereo mode if stereo source detected            
            if result["has_stereo_source"]:                 
                self.eval('setStringProperty("#RVDisplayStereo.stereo.type", string[]{"anaglyph"})')
        
        
        elif compare_mode=="contact_sheet":
            result      = self._add_sequence(playable, single_frame_position=single_frame_position )
            layout_node = self._rv_new_layout()
            
            track_list_string   = ",".join(['"%s"' % n for n in result["clip_node_list"] ])            
            self.eval('setNodeInputs("%(layout_node)s", string[]{%(track_list_string)s})' % vars())
            
            self.eval('setViewNode("%s")' % layout_node )
            
            
        else:                   # play in one of the compare modes
            # group into list of tracks
            track_list = self._group_playable(playable)
            track_node_list = []
            
            # add each track as a sequence
            for playable in track_list:
                result = self._add_sequence(playable) # <- all will produce the same mark_frame_list
                track_node_list.append( result['seq_node'] )
                
                # set stereo mode if stereo source detected
                if result["has_stereo_source"]: 
                    self.eval('setStringProperty("#RVDisplayStereo.stereo.type", string[]{"anaglyph"})')                    
                
            # create a stack and layout with the list of tracks
            track_list_string   = ",".join(['"%s"' % n for n in track_node_list ])
            
            stack_node          = self._rv_new_stack()
            layout_node         = self._rv_new_layout()
             
            self.eval('setNodeInputs("%(stack_node)s", string[]{%(track_list_string)s})' % vars())
            self.eval('setNodeInputs("%(layout_node)s", string[]{%(track_list_string)s})' % vars())
            
            # select the view depending on the mode            
            if compare_mode == "wipe":
                self.eval('setViewNode("%s")' % stack_node)
                self.eval('rvui.toggleWipe()')
                
                                
            elif compare_mode.startswith( "layout_" ):    
                self.eval('setViewNode("%s")' % layout_node)
                self.eval('setStringProperty("%s.layout.mode", string[]{"%s"})' % (layout_node, compare_mode.split("_")[1] ) )
                
            elif compare_mode == "blend":                
                self.eval('setViewNode("%s")' % stack_node)
                self.eval('setStringProperty("%s_stack.composite.type", string[]{"add"})' % stack_node )
                
        # mark the frames on the timeline
        for mf in result['mark_frame_list'][1:]:
            self.eval("markFrame(%s, true)" % (mf + 1))  
        

        self.eval('setIntProperty("#RVDisplayColor.color.Rec709", int[] {1});')
        self.eval('setIntProperty("#RVDisplayColor.color.sRGB", int[] {0});')
        self.eval('setFloatProperty("#RVDisplayColor.color.gamma", float[] {1.0});')
                        
        
        self.eval("setCacheMode(commands.CacheBuffer)")
        
        
    
    def _group_playable(self, playable):
        '''
        given list of clips, group them based on dept and shot_code
        return a list of tracks.  each track containing a sequence of clips
        
         
        '''
        # group playables
        clip_group = {}
        shot_play_range = {}
        dept_ver_count = {}
        
        shot_code_list  = []
        dept_list       = []
        '''
                   | shot_001   | shot_002   | ...
        anim       | v002, v001 | v001       |
        previs     |            | v003, v002 | 
        
        two summary data:
        shot_play_range:  { key: shot_code, value: duration}
        dept_ver_count: { key: dept, value max version for any particular shot 
        
        shot_code_list     = [shot_code]        # all the possible shot_code in play selection
        dept_list          = [dept]             # all the possible department in paly selection 
        
        '''
        
        for clip in playable:
            shot_code, dept = clip.get_meta('entity_code'), clip.get_meta('department')  
            
            if not clip_group.has_key(shot_code):
                clip_group[shot_code] = {}
                
            if not clip_group[shot_code].has_key(dept):
                clip_group[shot_code][dept] = []
                
            clip_group[shot_code][dept].append(clip)
            
            if shot_code not in shot_code_list:
                shot_code_list.append(shot_code)
                
            if dept not in dept_list:
                dept_list.append(dept)
        
        # TODO: now sort the shot code list in order of the movie 
        # TODO: also need to sort the version inside
        
        shot_code_list.sort()
        
        # TODO: this sorting should be refactor outside of rv_session so that it can be independent of production.
#         from tactic.tactic_config import REVIEW_TOOL_DEPTS
#         
#         sort_dept = REVIEW_TOOL_DEPTS
#         sort_dept.append("") # to handle external sources without dept
#  
#         dept_list.sort( lambda y, x: cmp(sort_dept.index(x), sort_dept.index(y)) )
        
        
        # eventually it returns list of list, or 2d list, list of tracks of shots
        for shot_code in shot_code_list:
            for dept in dept_list:
                if clip_group.has_key(shot_code) and clip_group[shot_code].has_key(dept):
                    print shot_code, ' ', dept, ' ', clip_group[shot_code][dept][0]
                    
                    if not shot_play_range.has_key(shot_code):                        
                        shot_play_range[shot_code] = list( clip_group[shot_code][dept][0].play_range() )
                        
                    for clip in clip_group[shot_code][dept]:
                        shot_play_range[shot_code][0] = min( shot_play_range[shot_code][0], clip.play_range()[0] )
                        shot_play_range[shot_code][1] = max( shot_play_range[shot_code][1], clip.play_range()[1] )
                        
                    
                    if not dept_ver_count.has_key(dept) or dept_ver_count[dept] < len(clip_group[shot_code][dept]):
                        dept_ver_count[dept] = len(clip_group[shot_code][dept])
                                        
        
        # now create the list of tracks
        track_list = []

        for dept in dept_list:                        
            for dept_track_index  in range(dept_ver_count[dept]):  # for each department, create N number of tracks
                new_track = []
                                
                for shot_code in shot_code_list:  
                    if clip_group.has_key(shot_code) and clip_group[shot_code].has_key(dept) and (dept_track_index) < len(clip_group[shot_code][dept]):
                        clip = clip_group[shot_code][dept][dept_track_index]
                    else:
                        clip = ClipSource()      # empty clip
                        clip.set_meta({"code":shot_code, "dept": dept, "description": "no publish"})
                    
                    clip.set_play_range(*shot_play_range[shot_code])
                    new_track.append(clip)
                
                track_list.append(new_track)


        # special case, if there are only two clips, then always put them on different track so then can be compared        
        if len(playable)==2 and len(track_list)!=2:
            frame_in  = min( playable[0].play_range()[0], playable[1].play_range()[0] )            
            frame_out = max( playable[0].play_range()[1], playable[1].play_range()[1] )
            
            playable[0].set_play_range( frame_in, frame_out )
            playable[1].set_play_range( frame_in, frame_out )
            
            track_list = [ [playable[0]], [playable[1]] ]
        

        return track_list
            
            
    def _rv_add_source(self, path):
        """
        Add the source to RV, the get the rv object name
        """        
        self.eval('addSource("%s")' % path)
        node = self._rv_list_sources()[-1]
        if node.endswith("_source"):
            node = node[:-len("_source")]
            
        return node

   
    def _rv_list_sources(self):
        result = self.eval('nodesOfType("RVFileSource")') # returns string[] {"sourceGroup000000_source", "sourceGroup000001_source"}
        
        result = re.search('{([\w,\ \"]+)}', result)
        if result:
            result = result.groups() [0]  # '"sourceGroup000000_source", "sourceGroup000001_source"'
            result = [ r.strip('" ') for r in result.split(",") ] # ['sourceGroup000000_source', 'sourceGroup000001_source']
            
            return result                
        
        
    def eval(self, command):    
        if not self.is_rv_connected():
            print "Warning: no RV connection." 
            return 
            
        if media.config.DEBUG_LOG: print "executing rv command: '%s'" % command
        
        result = self.rvc.remoteEvalAndReturn(command)
        
        if media.config.DEBUG_LOG: print "result: '%s'" % result
        
        global LAST_ACCESSED_RV_KEY
        LAST_ACCESSED_RV_KEY = self._session_key
        
        return result
    
    
    def is_rv_connected(self):
        """
        Test if there is currently an rv session opened and accepting commands
        """
        #if self.rvc != None and self.is_socket_connectable():
        if self._rv_proc!=None and self._rv_proc.poll()==None: 
            return True
        else:
            return False
    
    
    def is_socket_connectable(self):
        """
        Check it's possible to connect to the socket
        """         
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', self.port_num))
            s.close()
            return True
         
        except socket.error, e:
            pass
        
        return False
 
    
    def new_session(self):
        '''
        Create a new RV session, get the RV ROOT path and RV RAM from the config module.
        The RV path can override via a local config file, which is sourced by the config module. ex: c:/tmp/rv_path.txt
        
        '''
        self.port_num = get_next_free_port(self.host)
        
        os.chdir(os.path.normpath(RV_ROOT))
        
        # setting the cache size
        cache_setting = []
        
        if media.config.RV_DEFULT_CACHE_SETTING:            
            cache_setting = ['-l', '-lram', str(media.config.RV_RAM) ]            
        
        cmd = [ os.path.join(RV_ROOT, "bin", "rv"), '-network', '-networkPort', str(self.port_num) ] +  cache_setting
        
        
        print '*** rv cmd=[%s]' % (cmd)
        
        self._rv_proc = media.run_and_log_cmd(cmd, block=False, shell=False)
        rvNetwork.RV_SESSION_PROC = self._rv_proc 
        
        start_time = time.time()
        
        while (time.time() - start_time) < RV_CONNECT_TIME_OUT and not self.is_socket_connectable():
            time.sleep(0.05)
            
        if self.is_socket_connectable():
            self.rvc = rvNetwork.RvCommunicator("rv_session");
            self.rvc.connect (self.host , self.port_num)            
                        
            print 'RV connection established in %s ' % (time.time() - start_time)
        else:
            print 'RV connection failure via command %s ' % cmd
        
        
    
    def get_movie_range(self, source):         
        os.chdir(os.path.normpath(RV_ROOT))
        
        stdout, stderr = media.run_and_log_cmd('rvls -l "%s"' % source)    
        
        print stdout.split("\n")[1].split()
        
        return (0, int (stdout.split("\n")[1].split()[6]))
    
    
    
    def generate_thumb(self, source, frame_index, outpath):
        os.chdir(os.path.normpath(RV_ROOT))
        stdout, stderr = media.run_and_log_cmd(
                                              'rvio "%s" -t %s-%s -o "%s" -outres 200 200' % (
                                                          source,
                                                          frame_index, frame_index,
                                                          outpath
                                                          )
                                              
                                              )                
         
        if stderr:
            raise IOError, "Failed to generate thumb: %s " % stderr 




def get_source_meta(source):
    
    os.chdir(os.path.normpath(RV_ROOT))
    stdout, stderr = media.run_and_log_cmd(
                                          'rvls -x "%s"' % (
                                                      source,
                                                      )
                                          )
    
    source_start = re.search ("QT/Timecode/Start[\s]+([0-9]+)", stdout).groups()
    duration = re.search ("Duration[\s]+([0-9]+)[\s]+frames", stdout).groups()
    
    return {
            "source_start": int(source_start[0]),
            "duration":     int(duration[0])
            }
        
        

if __name__ == "__main__":
    rs = RvSession()    
    rs.new_session()
    
    for i in range(1):
        time.sleep(1)
        print '.....fps ', i, rs.eval("fps()")
        
