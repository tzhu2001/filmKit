'''
The clipStore.clip_source.ClipSource is a class representing a clip, which can be a movie or an image sequence.
It stores attributes like source path, source range, play range, source audio.

It can be decorated with production data via function set_publish_entity.  Hence the object can represent
a published clip or a local clip. 

Clip source also provides ability to resolve the source's range if not specified.  
For movie, it determines the source range using ffmpeg.    

Example Code:

##### create a mono movie clip source #####

MEDIA_SAMPLE_ROOT = "/systeme/softs/unit_test_data/"

movie_clip = ClipSource( MEDIA_SAMPLE_ROOT + "movie/movie_small.mov" )

# clip source automatically determine the range.
assert movie_clip.source_range() == (101, 177)        
assert movie_clip.source_path()  == MEDIA_SAMPLE_ROOT + "movie/movie_small.mov"         


##### create a stereo frame clip source #####

frames_clip = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.l.0101.jpg" )
 
# clip source automatically determine the range.
assert frames_clip.source_range()==(101, 109)

assert frames_clip.source_path(flg_stereo=True) == [ MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.l.####.jpg", 
                                                    MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.r.####.jpg"
                                                  ]
                                          

##### get the play data #####
# By default the play range is the same is the source range, but you can specify any range.
# If the play range is out of bounds, clip source will inform the head frame hold and tail frame hold.

mono_clip = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_mono_sequence/dummy_frame.l.####.jpg" )
assert mono_clip.source_range()==(101, 109)
assert mono_clip.get_play_data() == (None, 101, 109, None) 

# play out of range for head portion
cs = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_mono_sequence/dummy_frame.l.####.jpg",                                     
                            play_in = 80, play_out = 106 )

# play data show that you need to hold frame 101 for 21 frames
assert cs.get_play_data()==(21, 101, 106, None)

assert cs.play_range()==(80, 106)
  
'''
import os, sys, time, traceback, re, shutil, platform
import subprocess
import config
import media

from media import ffmpeg_util

LOG = config.get_logger()

class ClipSource:
    def __init__(       self, 
                         
                        source          = None,
                        preview         = None,
                         
                        resolved        = False,
                        
                        source_in       = None, 
                        source_out      = None, 
                        
                        play_in         = None, 
                        play_out        = None,
                         
                        source_audio    = None,
                        audio_offset    = 0,
                        
                        movie_start_index = 101,
                        
                        fps             = 24,
                        ):
        
        
        '''
        ClipSource is a class representing a clip, which can be a movie or an image sequence.
        
        @param source can be string movie path, frame sequence path, or list [ movie path, frame seq path ]
        @param resolved indicate if the source has been fully resolved and ready to be played.
               in order to be resolved, the source and preview must be a list, either mono or stereo.
               Also, the source in and source out is pre-determined.                
        
        @param source_in  [optional] auto resolve from source if not specified.
        @param source_out [optional] auto resolve from source if not specified.
        @param play_in    [optional] set the source_in if not specified.
        @param play_out   [optional] set the source_out if not specified.
        
        @param source_audio [optional] set the source audio
        @param audio_offset [optional] the audio offset in frames
        @param movie_start_index [optional - default = 101 ] for movie, can specify a display frame offset index.
        
        @param fps [optional - default 24] the fps for the source. 
        '''

        # store the source info    
        self._resolved_preview = self._resolved_source = resolved
        
        if resolved:
            assert type(source) in (tuple, list), "Source must be a list/tuple to be consider resolved."
            assert type(preview) in (tuple, list), "Source must be a list/tuple to be consider resolved."

            assert source_in    !=None, "Source in must be specified to be consider resolved."
            assert source_out   !=None, "Source out must be specified to be consider resolved."
            
            self._source        = source
            self._preview       = preview
            
        else:       
            if source!=None and source.strip() == "": 
                source = None
                    
            if preview!=None and preview.strip() == "":
                preview = None
                
            self._raw_source    = source
            self._raw_preview   = preview
            
            self._source        = None
            self._preview       = None
            

        # set the source frame range
        self._source_in     = source_in 
        self._source_out    = source_out    
                    
        # store the source audio info  
        self._source_audio   = source_audio 
        self._audio_offset   = audio_offset              
            
        # playback parameter
        self._play_in    = self._source_in if play_in==None else play_in  
        self._play_out   = self._source_out if play_out==None else play_out                    
        self._fps        = fps
        self._movie_start_index = movie_start_index # this is purely for displaying movie index so it doesn't start with 1.

        self._meta_data      = {}  # holds information about the clip, department, artist etc. for both published/unpublish        


    def movie_start_index(self):
        return self._movie_start_index
        
        
    def get_audio(self, offset_in_sec=False):
        '''
        @param offset_in_sec
        @return audio clip
        '''
        # note if it's an image sequence, there is an additional offset of from the beginning of the sequence.
        
        a_offset = self._audio_offset        
        
        if offset_in_sec:
            return self._source_audio, a_offset / self._fps
        else:
            return self._source_audio, a_offset 
        
        
    def get_fps(self):
        '''
        @return the fps of clip
        '''
        return self._fps

        
    def set_meta(self, meta_data, key=None):
        '''
        Set the meta data for the clip
        @param meta_data
        @param key
        '''
        if key:
            self._meta_data[key] = meta_data
 
        else:
            for md in meta_data:
                self._meta_data[md] = meta_data[md]


    def source_range(self):
        """
        Determine the source range in frames
        @return the source range
        @rtype: tuple
        """        
        if self._source_in==None or self._source_out==None:
            self.source_path()
            
        return self._source_in, self._source_out                    
             
         
    def get_meta(self, key=None, default=None):
        '''
        @default the default value if the key is pointing None
        @return the meta data associated with the clip of the key        
        '''
        if key:
            if self._meta_data.has_key(key):
                return self._meta_data[key]
              
            if self._meta_data.has_key("metadata") and self._meta_data["metadata"].has_key(key):
                value = self._meta_data["metadata"][key]
                return value if value!=None else default
                  
            else:
                return default
        else:
            return self._meta_data
            
   
    
    def get_play_data(self, flg_preview=False):
        """
        @param flg_preview play preview or the source
        @returns out of range head (frame count to hold the head frame),
                the source play range (frame_in, frame_out)
                out of range tail (frame count to hold the tail frame)                
                
                  ======
           =====          =====  case 1   
                  =========      case 2
               =========         case 3
               ============      case 4
                    ===          case 5
                  
        """
        
        if self._source_in==None or self._source_out==None:
            self.source_path()
        
        if self._play_in==None or self._play_out==None:    
            self._play_in, self._play_out = self._source_in, self._source_out

        # if play range is None, then use the source range
        if self._play_in==None or self._play_out==None:            
            play_meta = [ None, self._source_in, self._source_out, None ]
           
        elif self._play_in > self._source_out  or self._play_out < self._source_in: # case 1            
            play_meta = [ self._play_out-self._play_in + 1, None, None, None ]
        
        elif self._play_in >= self._source_in  and self._play_out > self._source_out:            # case 2
            play_meta = [ None, self._play_in, self._source_out, self._play_out- self._source_out ]
            
        elif self._play_in < self._source_in and self._play_out <= self._source_out:            # case 3
            play_meta = [ self._source_in - self._play_in, self._source_in, self._play_out, None ]
        
        elif self._play_in < self._source_in and self._play_out > self._source_out:            # case 4
            play_meta = [ self._source_in - self._play_in, self._source_in, self._source_out, self._play_out- self._source_out ]
        
        else:   # case 5            
            play_meta = [ None, self._play_in, self._play_out, None ]
        
        if self.source_type(flg_preview)=="movie" and self._movie_start_index!=None and self._play_in!=None: # and self.is_source_movie():
            play_meta[1], play_meta[2] = self._play_in - self._movie_start_index, self._play_out - self._movie_start_index
            
        return tuple(play_meta)
    
    
    def source_type(self, flg_preview):                
        if self.source_path(flg_stereo=False, flg_preview=flg_preview).split('.')[-1] in config.MOVIE_LIST:
            return "movie"
        else:
            return "frames"
        
    
    def set_play_range(self, play_in, play_out):
        '''
        Set the playrange
        @param play_in
        @param paly_out
        '''                  
        self._play_in    = min( play_in, play_out )
        self._play_out   = max( play_in, play_out )
         
         
    def play_range(self):
        '''
        @return the play range as tuple.
        @rtype: tuple
        '''
        # if it's already set, return that value
        if self._play_in!=None and self._play_out!=None:
            return self._play_in, self._play_out
        else:
            return self.source_range()
         
         
    def reset_play_range(self):
        '''
        If this is set to None, then during playback, this will be automatically be set to source range
        '''
        self.set_play_range(None, None)


    def is_stereo_source(self):
        '''
        @return if the source is stereo.
        @rtype: bool
        '''
        return len(self.source_path(flg_stereo=True))==2
    
    
    @staticmethod
    def _determine_range( path, movie_start_index ):
        '''
        determine the source range for movie or image sequence
        @param path of movie or image sequence
        @return path, source_in, source_out
        '''
        
        # resolve the movie source
        playable = []
        if path.split(".")[-1] in config.MOVIE_LIST:        
            left_mov    = path
            right_mov   = path.replace('.l.', '.r.')            
                            
            if left_mov == right_mov:
                right_mov = None
                                            
            if os.path.isfile(left_mov): 
                playable.append( left_mov )
                
            if right_mov and os.path.isfile(right_mov):
                playable.append( right_mov )
                
            if not playable:
                print "Warning can not resolve movie source from %s." % _raw_movie_source                
                return 
              
            source_in, source_out = ffmpeg_util.get_movie_range( left_mov ) #, self._get_thumb_root() )
            
            source_in  += movie_start_index
            source_out += movie_start_index
            
            return playable, source_in, source_out
                   
        # resolve the frame source        
        else:            
        
            left_result = right_result = None
            left_frame  = path
            right_frame = path.replace('.l.', '.r.')
            
            if left_frame == right_frame:
                right_frame = ""
            
            left_result  = media.query_img_seq( left_frame )
            
            if left_result:
                if type(left_result) in (list, tuple):
                    left_result = left_result[0] # if left_frame is a directory.
                    
                playable.append( left_result['template_path'] )

            if right_frame:
                right_result = media.query_img_seq( right_frame )
                
            if right_result:
                if type(right_result) in (list, tuple):
                    right_result = right_result[0] # if right_frame is a directory.
                
                playable.append( right_result['template_path'] )
            
            # if it's stereo image sequence, left and right should have same ranges
            if left_result and right_result and left_result.has_key('ranges'): 
                assert left_result['ranges']==right_result['ranges'], \
                            "The frames range of left (%s) does match that of right(%s)" % (left_result['ranges'], 
                                                                                            right_result['ranges'])
                            
            source_in = left_result['in']
            source_out = left_result['out']
                            
        if not playable:
            LOG.warning( "Warning can not resolve source from %s." % _raw_movie_source )
            
        return playable, source_in, source_out    
        
    
    def _resolve_source_path(self, flg_preview=False):
        '''
        Resolve the source range for either the preview or the source.
        '''
        if flg_preview:
            if not self._resolved_preview and self._raw_preview:
                result = self._determine_range( self._raw_preview, self._movie_start_index )
                if result:
                    self._preview, self._source_in, self._source_out = result
                    
                self._resolved_preview = True            
            
            return self._preview
            
        else: 
            if not self._resolved_source and self._raw_source:            
                result = self._determine_range( self._raw_source, self._movie_start_index )
                
                if result:
                    self._source = result[0]
                    if self._source_in==None:   self._source_in = result[1]
                    if self._source_out==None:  self._source_out = result[2]
                    
                self._resolved_source = True
            
            return self._source
        
    
    def source_path(self, flg_stereo=False, flg_preview=False):
        '''
        @param flg_stereo 
        @param source_preference: one of 'preview', 'source'
        @rtype: list [string]
        '''
        result =  self._resolve_source_path( flg_preview )
        
        if result==None:
            result = self._resolve_source_path( not flg_preview )
        
        if result:
            return result if flg_stereo else result[0]
        
        
        
              
    def is_published(self):
        '''
        If the clip is tracked in production db or it's a local clip.
        '''
        return self._published_entity!=None 
     
   
    def set_publish_entity(self, version):
        '''
        Decorate the clip source with a publish entity 
        @param version the frame submission entity
        '''        
        self._published_entity = version
         
         
    def publish_entity(self):
        '''
        @return the associated publish entity
        @rtype: tina.entity_factory.FrameSubmission
        '''
        return self._published_entity
         

        
        