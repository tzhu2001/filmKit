"""
 \namespace media.ffmpeg_util Module introspects media files and return in python friendly data via ffmpeg, ffprobe
 
 ffprobe -show_streams -pretty 
"""
import os, re, subprocess

from media.config import MOVIE_FORMATS, IMAGE_FORMATS, FF_ROOT

def get_media_info(media_path):
    """
    Given the path the the audio or movie, return the data return by ffprobe
     
    @param media_path is path to audio or movie file.
    @return dictionary of meta data. encoding, length, resolution, etc.
    """
    meta    = {}
    rg_vid  = re.compile('Stream[#\w\s:\(\)]+Video:\s([\w_]+).*')
    rg_aud  = re.compile('Stream[#\w\s:\(\)]+Audio:\s([\w_]+).*')
    rg_dur  = re.compile('Duration: ([0-9:.]+), start: ([0-9.]+),')
    rg_sec  = re.compile('([0-9]{2}):([0-9]{2}):([0-9]{2})[.]*([0-9]*)')
    
    rg_res  = re.compile('[0-9]+x[0-9]+')
    rg_rate = re.compile('[0-9]+\s[\w]b/s')
    rg_fps  = re.compile('([0-9]+)\sfps')    
    
    rg_channel  = re.compile('([0-9]+)\schannels')    
    rg_hertz    = re.compile('[0-9]+\sHz')
        
    command = "ffprobe " + media_path
    raw_out = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    
    raw_out = '\n'.join(raw_out)    
    
    # search the probe output for video and audio stream data
    video_info = rg_vid.search( raw_out )
    audio_info = rg_aud.search( raw_out )
    duration   = rg_dur.search( raw_out )
    
    # parse the raw time info for information
    if duration:
        meta['duration'] = duration.groups()[0]
        h, m, s, f =  [ int(i) for i in rg_sec.search( meta['duration'] ).groups() ]
        
        meta['duration_sec'] = h * 3600 + m * 60 + s + float('.%s' % f ) 
        
    
    # parse the raw video string for information 
    if video_info and duration:  # check for duration since ffprobe return video steam data even for text file.
        meta['video_raw_info'] = video_info.group()
        
        tokens = [ t.strip() for t in meta['video_raw_info'].split(',') ]        
        meta['video_codec'] = video_info.groups()[0].strip()
        
        for t in tokens:
            if rg_res.search(t):
                meta['height'], meta['width']   = rg_res.search(t).group().split('x')
            
            if rg_rate.search(t):
                meta['video_bitrate']           = rg_rate.search(t).group()
        
            if rg_fps.search(t):
                meta['fps']                     = int(  rg_fps.search(t).groups()[0] )
                meta['duration_frame_float']    = meta['duration_sec'] * meta['fps']
                meta['duration_frame']          = int( round( meta['duration_frame_float'] ) )
                
        
    # parse the raw audio string for information
    if audio_info:
        meta['audio_raw_info'] = audio_info.group()    
        tokens = [ t.strip() for t in meta['audio_raw_info'].split(',') ]
        
        meta['audio_codec'] = audio_info.groups()[0].strip()
        
        for t in tokens:
            if rg_rate.search(t):
                meta['audio_bitrate']   = rg_rate.search(t).group()
                
            if rg_channel.search(t):
                meta['audio_channels']  = int( rg_channel.search(t).groups()[0] )        

            if t.strip() == 'mono':
                meta['audio_channels']  = 1        

            if rg_hertz.search(t):
                meta['audio_hertz']     = rg_hertz.search(t).group()
    
    if meta.has_key('fps'):           
        meta['media_type'] = 'movie'
    
    elif meta.has_key('duration'):
        meta['media_type'] = 'audio'
    
    return meta



def _get_movie_raw_info( source, cache_source_dir=None):
    """
    use ffprobe to get and cache the image information, ex: width and height etc.
    """      
    
    if cache_source_dir: # if the data is cached.
        outpath = os.path.join(cache_source_dir, os.path.split( source )[1] + ".txt")
        
        print "Raw movie info cached to %s..." % outpath

        # check if output already exsit:
        if os.path.exists(outpath):
            content = open(outpath).read()

            if "Duration" in content or "duration" in content:  # search for Duration in content
                return content
        
    ffprobe = FF_ROOT + '/ffprobe'
    
    stdout, stderr = media.run_and_log_cmd( ffprobe + " " +  '"%s"' % source, root=FF_ROOT)
#     self.movie_meta_dict[source] = stderr
    content = stderr

    # if it's a publish source, cache the raw ffprobe data
    if cache_source_dir:  # source.lower().startswith( config.PUBLISH_ROOT.lower() ): # check it's published
        print "Cached movie raw info into file..." 
        f = open(outpath, "w")
        f.write(stderr)
        f.close()

    return content

import media
def get_source_range( source):
    if source.split('.')[-1] in IMAGE_FORMATS:
        return media.query_img_seq(source)

    elif source.split('.')[-1] in MOVIE_FORMATS:
        return get_movie_range(source)


def get_movie_range( source, cache_info_path=None):
    """
    @param_info_path is where the ffprobe out info lives, caches the data so it doesn't need to reprocess info.
    return the movie range by parsing the row image information ffprobe output.        
    """
    result = re.search("Duration: ([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+),", 
                       _get_movie_raw_info(source, cache_info_path ))

    if result:
        result = [ int(r) for r in result.groups() ]

        h, m, s, ms = result
        seconds = h*60*60 + m*60 + s + ms/100.0

        frames = seconds * 24

        return (0, int(round(frames))-1 )

    else:
        return (-1, -1)


def get_source_size( source):
    if source.split('.')[-1] in IMAGE_FORMATS:
        source_meta = media.get_image_sequence_pattern( source, padding_format="%", flg_as_fragments=True)

        if type(source_meta["original_pad_type"])!=int: # the user has specify a template path rather than an index
            # set it to the first frame
            source = source_meta["template_path"] % media.determine_image_sequence(source, return_meta=True)["in"]

        return get_image_size(source)

    elif source.split('.')[-1] in MOVIE_FORMATS:
        return get_movie_size(source)


def get_movie_size( source, cache_source_dir):
    """
    return the movie dimensions by parsing the row image information ffprobe output.
    """
    result = re.search("([0-9]{2,5})x([0-9]{2,5})[\ \,]{1}", _get_movie_raw_info(source, cache_source_dir))

    if result:
        result = [ int(r) for r in result.groups() ]
        w, h = result

        return w, h

    else:
        return -1, -1


def get_image_size( source):
    """
    return the image dimensions by parsing imagick identify result
    """

    raw_out, err_out = media.run_and_log_cmd('identify "%s"' % source, root=config.MAGICK_ROOT)
    result = re.search("\ ([0-9]+)x([0-9]+)\ ", raw_out)
    if result:
        return tuple( [ int (i) for i in result.groups() ] )


def generate_movie( source, frame_in, frame_out, movie_out=None, source_audio=None, meta_data=""):
    """
    Generate the preview movie, return the movie path
    """
    '''ffmpeg -f image2 -sameq -i C:\tmp\seq\jpg\q040s0400_r_v007.%04d.jpg c:\tmp\ffmpeg1.mov'''

    # need to renumber it to start from 1 for ffmepg to operate on them
    i=1
    new_index_path = os.path.join( os.path.split(source)[0], "processed.%04d." + source.split(".")[-1] )
    for x in range (frame_in, frame_out):
        os.rename(source % x,  new_index_path % i )
        i+=1

    # now create the movie, clean up previous output movie, if any
    if movie_out==None:
        movie_out = os.path.join( os.path.split(source)[0], "processed.mov" )

    if os.path.isfile(movie_out):
        os.remove(movie_out)

    if type(meta_data)==str:        # metadata for the header
        metastring = ' -metadata title="%s" ' % meta_data
    else:
        metastring = ""


    cmd = 'ffmpeg -f image2 -sameq %(metastring)s -i "%(new_index_path)s" -y "%(movie_out)s"' % vars()
    stdout, stderr = media.run_and_log_cmd(cmd, root=FFROOT)

    if not os.path.isfile(movie_out):
        print "runing command: ", cmd
        raise IOError, "Failed to generate movie: %s " % stderr
    else:
        return movie_out

    

def generate_thumb( source, frame_index=None, thumb_out=None, thumb_width=240):
    """
    generate the thumb for either a movie or a frame source
    """        
    # determine thumb out, and also clean up
    assert thumb_out!=None, "The thumb out path must be provided to generate the thumbnail." 

    if os.path.isfile(thumb_out):
        os.remove(thumb_out)

    # generate thumb
    if source.split('.')[-1] in MOVIE_FORMATS:
        print "Generate thumb from movie source %s..." % source
        return generate_thumb_movie(source, frame_index, thumb_out, thumb_width)

    elif source.split('.')[-1] in IMAGE_FORMATS:
        print "Generate thumb from image source %s..." % source
        return generate_thumb_image(source, frame_index, thumb_out, thumb_width)

    else:
        print "Warning: can not generate thumbnail for unsupported source format '%s' " % source
    

def generate_thumb_image( source, frame_index=None, thumb_out=None, thumb_width=240):
    '''
    Generate thumbnail of an image.
    @param source the source of the thumbnail
    @param frame_index
    @param thumb_out out path for the thumbnail
    @param thumb_width the width of the thumbnail
    '''
    if frame_index==None:
        meta        = media.determine_image_sequence(source)
        _in, _out   = meta["in"], meta["out"]
        frame_index = (_in + _out) / 2

    seq_template = media.get_image_sequence_pattern(source, "%")        

    if "%" in seq_template:
        source      = seq_template % frame_index
        
    
    if not os.path.isfile( source ):
        return

    w, h = get_image_size(source)
    tw = thumb_width

    th = float(tw)/w * h
    tw = int(tw)
    th = int(th)

    command = "convert -resize %sx%s " % (tw, th)

    if source.split(".")[-1] in ("tif", "tiff", "exr", "png"):
        command += ' -background "rgb(200,200,200)" -flatten -gamma 2.2 '

    command += ' "%(source)s" "%(thumb_out)s"' % vars()

    stdout, stderr = media.run_and_log_cmd(command, root=config.MAGICK_ROOT)

    if not os.path.isfile(thumb_out):
        print "runing command: ", command
        raise IOError, "Failed to generate thumb: %s " % stderr
    else:
        return thumb_out


def generate_thumb_movie( source, frame_index=None, thumb_out=None, thumb_width=240):
    '''
    Generate thumbnail of a movie.
    @param source the source of the thumbnail
    @param frame_index
    @param thumb_out out path for the thumbnail
    @param thumb_width the width of the thumbnail
    '''
    '''ffmpeg  -itsoffset -4  -i test.avi -vcodec mjpeg -vframes 1 -an -f rawvideo -s 320x240 test.jpg'''

    w, h = get_movie_size(source, os.path.split(thumb_out)[0] )
    tw = thumb_width
    th = float(tw)/w * h
    tw = int(tw)
    th = int(th)

    if frame_index==None:
        fin, fout = get_movie_range(source, os.path.split(thumb_out)[0] )
        offset_sec= 0 #(fin+fout) /2  / 24.0
    else:
        offset_sec= 0 #frame_index / 24.0

    ff_root = config.FF_ROOT

    cmd = [ ff_root + '/ffmpeg' if ff_root else 'ffmpeg', 
            '-itsoffset', offset_sec, '-i', source, '-sameq', '-vframes', 1, '-s', '%sx%s' % (tw, th), '-y', thumb_out ] 
    
    stdout, stderr = media.run_and_log_cmd( [str(item) for item in cmd], root=ff_root, shell=False)

    if not os.path.isfile(thumb_out):
        print "runing command  : ", cmd
        raise IOError, "Warning: Failed to generate thumb: %s " % stderr
    else:
        return thumb_out
    
    
    
    

def trim_audio(audio_path, trim_audio_path, trim_offset, duration):
    # audio offset is adjusted becuase the submitted offset is the offset relative to the shot duration
    # where SOX process use the relative offset

    # clip long audios
    trim_offset = float(trim_offset) / config.FPS
    duration = float(duration) / config.FPS

    cmd_list = [config.SOX_ROOT + "/sox", audio_path, "-t", "wav", trim_audio_path, "trim", str(trim_offset), str(duration)]

    print "trimming audio with command %s " % (" ".join(cmd_list))

    import subprocess
    result = subprocess.Popen(cmd_list,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          ).communicate()

    print result    