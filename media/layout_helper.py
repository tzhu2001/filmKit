def bootstrap_burin( sequencer_shot, movie_path, shot_start, shot_end, width=1920, height=1080, font_size=35.0 ):
    '''
    This is a hack for bootstrapping the simple layout playblast script.
    
    The parent script loops around the sequencer shot, and playblast to a movie, 
    this script is injected in that loop towards the end 
    and use RVIO to make some burnin on the resulting playblast movie.
    
    script needs to be run within maya.
    '''
    from media import rvio_util
    import re 
     
    reload(rvio_util)    
    
    print "Annotating movie via RVIO :", movie_path
    
    audio_path = focal_length_list = scene_path = ""
    audio_offset = 0
    shot_name = str(sequencer_shot)
    
    if sequencer_shot:
        from maya import cmds
        from media import maya_util
        reload(maya_util)
        
        # get the sequence_shot
        current_camera  = cmds.listConnections( str(sequencer_shot) + '.currentCamera' )
        camera_node     = cmds.listRelatives(current_camera, allDescendents=True, type='camera')
                
        # query the camera focal data
        focal_length_list = []
        if camera_node:
            for t in range(shot_start, shot_end+1):
                focal_ = cmds.getAttr("%s.focalLength" % camera_node[0], time=t)
                focal_ = str( int(round( focal_ * 10  )) )
                focal_length_list.append( focal_[:-1] + "." + focal_[-1:] )            
        
        # query other scene data
        scene_path = cmds.file( query=True, sceneName=True)                
        scene_name = re.search( "(sc[0-9]{3,5})", scene_path )
        
        if scene_name:
            shot_name =  str( scene_name.group() + '-' + shot_name )
        
        # get the scene audio
        audio_path, audio_offset = maya_util.get_scene_audio()
    
    print "audio path:", audio_path
    print "audio offset:", audio_offset
    
    movie_out_path = rvio_util.make_movie_burnins(       
                                        source_path = movie_path, 
                                        frame_width = width, 
                                        frame_height = height, 
                                        
                                        frame_start = shot_start, 
                                        frame_count = shot_end - shot_start + 1, 
                                        
                                        shot_name   = shot_name, 
                                        focal_length_str = ",".join(focal_length_list), 
                                        
                                        dependent_file  = scene_path, 
                                         
                                        font_size   = font_size, 
                                        opacity     = 0.95, 
                                        film_aspect = 2.39,
                                        
                                        audio_path   = audio_path,
                                        audio_offset = audio_offset,
                                        
                                        codec = 'mjpa')    

    # move original file.
    import shutil

    import os
    print "rename %s to %s..." % ( movie_path, movie_path + '.ori' )
    os.rename(movie_path, movie_path + '.ori')
    print "rename %s to %s..." % ( movie_out_path, movie_path )
    os.rename(movie_out_path, movie_path)

    print "Successfully made burn in to movie: ", movie_path

