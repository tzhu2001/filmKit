'''
\namespace media.rvio_util 
Collection of useful media function through the rvio.
'''
# PyBlast per shot
import subprocess, os

# configurations
RVIO_PATH = "/systeme/softs/rez/packages/rv/4.0.10/bin/rvio"

# query for meta data
import getpass, time

def make_movie_burnins( source_path,                         
                        
                        frame_width, 
                        frame_height,

                        frame_start = 101, 
                        frame_count = -1, 
                        
                        dest_path   = None,
                        
                        # burn in data:
                        shot_name = "",
                        focal_length_str = "",
                        
                        dependent_file  = "",                        
                        
                        artist          = "",
                        comment         = "",
                        date            = "",       
                        
                        # burn in parameter
                        font_size       = 30,
                        opacity         = 0.95,
                        
                        #   
                        film_aspect     = 2.39,
                        codec           = 'x264', 
                        fps             = 24,
                        
                        
                        audio_path      = "",
                        audio_offset    = 0
                                 
                        ):
    '''
    Given path to movie or image sequence (only movie supported at the moment), create a movie with the burn ins
    
    @param source_path path to the movie or image sequence
    @param dest_path path for the resulting movie
    @param frame_width
    @param frame_height
    
    @param frame_start the frame start index: the burnin start index.
    @param frame_count the duration of the clip in frames: solely used for display purpose
    
    @param shot_name the prod name of the shot
    @param focal_length_str the command delimited string of focal lengths
    @param dependent_file the dependent file name
    
    @param artist [optional] burnin data 
    @param comment [optional] burnin data
    @param date [optional] burnin data
    
    @param font_size [optional] the burnin font size
    @param opacity [optional] the burin film gate matte opacity, the burnin opacity
    @param film_aspect [optional] the thickness of the film gate matte.
    
    @param codec the rvio compress codec {'x264', 'mjpa' (motion jpeg: default) }, "rvio -formats" to see full list.
    
    @return the path of the generated movie.
    
    '''
    _user     = artist if artist else getpass.getuser()
    _date     = time.strftime("%Y/%m/%d",   time.localtime())
    _time     = time.strftime("%H:%M",      time.localtime())
    
    top_right = " | ".join( [_user, _date, _time] )
    
    flg_replace_ori_file = False
    
    if not dest_path:
        dest_path = source_path + "_burnin.mov"  
        flg_replace_ori_file = True # replace original file.    
    
    if not focal_length_str:
        focal_length_str = "n/a"
    
    # the parameters to the rvio can'be be empty string, so add a space
    if not dependent_file: 
        dependent_file = " "
    else:        
        dependent_file = os.path.split( dependent_file)[-1]
    
    # special handle for x264, there issue with older mmepg library (default of rvio) that animation does not play, but scrubs. 
    if codec=='x264':
        os.environ['RV_ENABLE_MIO_FFMPEG'] = "1"
        codec = 'libx264' 
    
    if audio_path:
        audio_path = '"%s" -ao %s' % (audio_path, float(audio_offset - frame_start)/fps )
    else:
        audio_path = ""
    
    command = RVIO_PATH + ' [ "%(source_path)s" %(audio_path)s ] -o "%(dest_path)s" -overlay tlp_burn "%(dependent_file)s" " " "%(top_right)s" '
    command += '"shot: %(shot_name)s" %(film_aspect)s "%(focal_length_str)s" "movie" %(frame_start)s %(frame_count)s '
    command += '%(opacity)s %(font_size)s -outres %(frame_width)s %(frame_height)s -codec %(codec)s -outfps %(fps)s'
    command = command % vars()
       
    print "subprocess command > %s" % command 
    proc = subprocess.Popen( command, stdout= subprocess.PIPE, stderr=subprocess.PIPE, shell=True);
    
    stdout, stderr = proc.communicate()
    
    if not os.path.isfile(dest_path):
        raise IOError, "Failed to generate movie to '%s'. %s" % (dest_path, stderr if stderr else "")
    else:
        print "Generated movie successfully to %s. " % dest_path
        
        return dest_path