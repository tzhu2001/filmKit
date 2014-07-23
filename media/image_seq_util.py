import os, re

TEST_COUNT = 0

def format_img_seq_pattern(filepath, padding_format="#", flg_as_fragments=False, frame_in=None, frame_out=None):
    """
    @param filepath can be c:\some\path\test.1234.png
                           c:\some\path\test.####.png
                           c:\some\path\test.%02d.png
                           c:\some\path\test.@@@@@@.png
                        
    
    @param padding_format can be one of "#", "%", "exp"
    @param flg_as_fragment return path as fragments instead of a string
    
    
    @return formatted path, ie: 
                            format:  result:
                            #        c:\some\path\test.####.png                            
                            %        "c:\some\path\test.%04d.png
                            -@       "c:\some\path\test.1-18@@@@.png" # this requires frame_in and frame_out
                                
    Currently assumes the padding is from 3-9
    
    if flg_as_fragments is True:
    
    return {
                "dir":                  filedir, 
                "header":               file_header, 
                "padding_string":       file_padding_string, 
                "ext":                  file_ext,
                "seq_index":            seq_index,
                "original_pad_type":    original_pad  <- the original padding type, one of {#,%, or the index as int)
                }
    
    
    
    
    """
       
    # format to common
    filedir, filename = os.path.split(filepath)    
    
    padding_count   = None
    seq_index       = None
    original_pad    = None
    file_header     = None
    file_padding_string = None
    file_ext        = None
    left_delimiter  = "."
    right_delimiter = "."
    
    if padding_count==None:
        MATCH_EXPR      = "([\.|_]{1})([0-9]{3,9})([\.|_]{1})"
        result          = re.search(MATCH_EXPR, filename)          
    
        if result: 
            left_delimiter, _index, right_delimiter = result.groups() 
            padding_count   = len ( _index )
            seq_index       = int ( _index )
            original_pad    = seq_index
            
            file_header, file_ext =  filename[:result.start()], filename[result.end():]
            
    if padding_count==None:
        MATCH_EXPR = "([\.|_]{1})([#]{3,9})([\.|_]{1})"
        result = re.search(MATCH_EXPR, filename)
    
        if result: 
            left_delimiter, _index, right_delimiter = result.groups()
            padding_count   = len ( _index )
            original_pad    = "#"
            
            file_header, file_ext =  filename[:result.start()], filename[result.end():]

     
    if padding_count==None:
        MATCH_EXPR = "([\.|_]{1})([@]{3,9})([\.|_]{1})"
        result = re.search(MATCH_EXPR, filename)
    
        if result:
            left_delimiter, _index, right_delimiter = result.groups() 
            padding_count   = len ( _index )
            original_pad    = "@"
            
            file_header, file_ext =  filename[:result.start()], filename[result.end():]

        
    if padding_count==None:
        MATCH_EXPR = "([\.|_]{1})%0([3-9])d([\.|_]{1})"
        result = re.search(MATCH_EXPR, filename)
    
        if result: 
            left_delimiter, _index, right_delimiter = result.groups()
            padding_count   = int ( _index )
            original_pad    = "%"
            
            file_header, file_ext =  filename[:result.start()], filename[result.end():]
    
    # not part of a sequence:
    if padding_count==None:
        if flg_as_fragments:
            return None # there are no image sequences
        else:
            return filepath        
            
    # formating to destination format
    if padding_format==None and original_pad!=None:
        padding_format = original_pad
        
    elif padding_format==None:
        padding_format = "#"
            
    if padding_count and padding_format=="#":
        file_padding_string = "#" * padding_count
        
    elif padding_count and padding_format=="@":
        file_padding_string = "@" * padding_count        

    elif padding_count and padding_format=="-@":
        if frame_in==None or frame_out==None:
            raise IOError, "To format '-@', you must also specify the frame_in and frame_out."
        file_padding_string = "%s-%s" % (frame_in, frame_out) +  "@" * padding_count        
        
    elif padding_count and padding_format=="%": 
        
        file_padding_string = "%0" + str(padding_count) + "d"
        
    elif padding_count and padding_format=="exp":
        file_padding_string = "%0" + str(padding_count) + "d"
        
    elif padding_count and padding_format=="%[]":
        file_padding_string = "%0" + str(padding_count) + "d" + "[%s:%s]" % (frame_in, frame_out)
    
    elif padding_count:
        raise KeyError, "the padding_format '%s' is not supported" % padding_format 
    
    formated_file_name = file_header + left_delimiter + file_padding_string + right_delimiter + file_ext
    
    if flg_as_fragments:
        return {
                "dir":                  filedir, 
                "header":               file_header, 
                "padding_string":       file_padding_string, 
                "ext":                  file_ext,
                "seq_index":            seq_index,
                "original_pad_type":    original_pad,
                "padding_count":        padding_count,
                "template_path":        os.path.join(filedir, formated_file_name ),
                "left_delimiter":       left_delimiter,
                "right_delimiter":      right_delimiter,
                }
    
    else:        
        return os.path.join(filedir, formated_file_name )   

from operator import itemgetter
from itertools import groupby

def group_continue_range(data):
    """
    @param data:
    
    """    
    data.sort()
    ranges = []
    for k, g in groupby(enumerate(data), lambda (i,x):i-x):
        group = map(itemgetter(1), g)
        ranges.append((group[0], group[-1]))
    
    return ranges        


def range_list_to_string(range_list):
    """
    @param list of frame tuples
    @return the frame ranges string
    
    Given [[1,3],[5,5],[8,9]] return 1-3,5,8-9
    """

    result = []
    for r in range_list:
        if r[0]!=r[1]:
            result.append( "%s-%s" % (r[0], r[1]) )
        else:
            result.append( str(r[0]) )
            
    return ",".join(result)



def get_range_tuple(frame_in, frame_out=None):
    """
    @param frame_in [int or str] frame in as integer or a frame ranges string.
    @param frame_out [optional]
    @return list of tuples of frame ranges.
    
    Ex:
    given frame_in = "1-3,4,6-10"    frame_out = ""             -> return [ [1,3],[4,4], [6,10] ]
    given frame_in = 1               frame_out =  9             -> return [ [1,9] ]
    given frame_in = "1"             frame_out =  "9"           -> return [ [1,9] ]
    """
    if type(frame_in)==int or type(frame_in)==float or frame_in.isdigit():
        frame_range_tuples = [ [int(frame_in), int(frame_out)] ]
        
    elif type(frame_in) in (str, unicode):
        frame_range_tuples = []
        
        for frame_tuple_str in frame_in.split(","):
            if "-" in frame_tuple_str:
                frame_in, frame_out = [ int(f) for f in frame_tuple_str.split('-') ]
                frame_range_tuples.append( [frame_in, frame_out] )
                
    
    return frame_range_tuples
    
    
def query_stereo_source(query_path):
    """
    @param query_path the source folder path that contains mono or stereo image sequence.
    @return the stereo source range  
    
    This work in conjunction with determine image sequence, but looking at the result of the images and
    returning a stereo source if possible.
    """
    result = query_img_seq(query_path)
    
    if not type(result)==list:
        return [ result ]
        
    new_result = result[:2]  # we just care about the first two result, if there are two
    
    new_result.sort(lambda x,y: cmp(x['header'], y['header']) ) # left before right
    
    if len(new_result) == 2 and ( new_result[0]['header'].split(".")[:-1] == new_result[1]['header'].split(".")[:-1]):
        return new_result
    
    
    


def query_img_seq(query_path):    
    """
    @param query_path the template path or a folder containing image sequence.
    
    # if given a folder (ex: /mnt/test), then return all the possible image sequences
    # if given a template path (ex: /mnt/test/img_seq.0001.jpg), then return one that matches the template path
    
    @return all the sequences like so:
      Note: if the query_path specifies a folder, it will return a list of hash of all possible sequences
            if the query_path specifies a template path, it will return the matching sequence, if any.
        [{'dir': 'R:/shot_vault/tnj/lgt/q130/s0010/v006/linked_frames',
          'ext': 'exr',
          'header': 'tnj_q130_s0010_lgt.l',
          'in': 101,
          'out': 588,
          'padding_string': '######',
          'ranges': [(101, 588)],
          'ranges_string': '101-588',
          'template_path': 'R:/shot_vault/tnj/lgt/q130/s0010/v006/linked_frames/tnj_q130_s0010_lgt.l.######.exr'},
          
         {'dir': 'R:/shot_vault/tnj/lgt/q130/s0010/v006/linked_frames',
          'ext': 'exr',
          'header': 'tnj_q130_s0010_lgt.r',
          'in': 101,
          'out': 588,
          'padding_string': '######',
          'ranges': [(101, 588)],
          'ranges_string': '101-588',
          'template_path': 'R:/shot_vault/tnj/lgt/q130/s0010/v006/linked_frames/tnj_q130_s0010_lgt.r.######.exr'}]
              
    """
    search_pattern = None # if the a search file template has been specified
    
    if not query_path:
        raise IOError, "Query path can not be empty."
    
    elif os.path.isdir(query_path):
        search_dir = query_path
        
    else:
        result = format_img_seq_pattern(query_path, padding_format="#", flg_as_fragments=True)
        if result==None or type(result)==str:
            print "Warning: file path does not point to a image sequence: %s" % query_path.replace("\\", "/")
            
            return {
                "in":               1,
                "out":              1,
                "template_path":    query_path.replace("\\", "/")
                }            
        
        else:
            search_pattern      = result
            search_dir          = search_pattern["dir"] 
    
    # examine every file and filter for the image sequence files
    if os.path.isdir( search_dir ):
        all_files = os.listdir( search_dir )
    else:
        raise KeyError, "Query path '%s' does not exist." % search_dir
     
    img_seq_searches = [ ( f, 
                           format_img_seq_pattern(f, padding_format="#", flg_as_fragments=True) ) 
                           for f in all_files ] # store tuple, (original file name, match result)
    
    img_seq_searches = [ f for f in img_seq_searches if type(f[1])==dict ] # filter one with no match result: ie not a seq file
    
    # now group the files based on pattern (header, padding_string, ext)
    img_seq_group = {}
    for _filename, _pattern_result in img_seq_searches:
        key = ( _pattern_result["header"],                 
                _pattern_result["padding_string"], 
                _pattern_result["ext"],
                _pattern_result["left_delimiter"],
                _pattern_result["right_delimiter"],
                 
                 )
        
        if key not in img_seq_group: 
            img_seq_group[key] = []
            
        img_seq_group[key].append(_pattern_result)
            
    
    # now amalgamate to get first frame, last frame, for each pattern
    image_seq_info_hash = {}
    for key in img_seq_group.keys():
        header, padding, ext, l_delimiter, r_delimiter = key
        
        file_list =  img_seq_group[key] # all the files of the particular pattern        
        
        # get the frame_in and frame_out
        index_list = [ k["seq_index"] for k in file_list ]
        index_list.sort()
        
        _in, _out = index_list[0], index_list[-1]        
        
        ranges = group_continue_range(index_list)
        
        image_seq_info_hash[key] = {
                "in":               _in,
                "out":              _out,
                "ranges":           ranges,
                "ranges_string":    range_list_to_string(ranges),
                "dir":              search_dir,
                "header":           header,
                "padding_string":   padding,
                "ext":              ext,
                "template_path":    search_dir + "/" + "%s%s%s%s%s" % (header, l_delimiter, padding, r_delimiter, ext) 
                }        
        
    
    # now return the results
    image_seq_info_list = image_seq_info_hash.values()
    
    # sort the list of image sequences in result, from longest sequence first.
    image_seq_info_list.sort(lambda y, x: cmp(x["out"]-x["in"], y["out"]-y["in"]) ) #    
            
    if os.path.isdir(query_path):        
        return image_seq_info_list

    else: # it's a file template. then must match the file template
        file_name_template = (search_pattern["header"], 
                              search_pattern["padding_string"], 
                              search_pattern["ext"],
                              search_pattern["left_delimiter"],
                              search_pattern["right_delimiter"],                              
                               )
        
        if image_seq_info_hash.has_key(file_name_template):
            return image_seq_info_hash[file_name_template] 
        
        

    
    
def len_img_seq_padding(filepath):
    """
    Given the path to the image sequence, return the number of padding in filepath, 
    it's also a good way to determine if it's part of image sequence or not.
    
    If it's not part of sequence, it will return None
    
    @param filepath
    @return number of padding.
    """
    result = format_img_seq_pattern(filepath, padding_format="#", flg_as_fragments=True)
    
    if type(result)==dict:        
        return len(result["padding_string"])
    
    else:
        return None
    
    
    
import datetime
def relative_date(d, default="%b %d %Y %I:%M%p"):
    '''
    Given a date, return the relative time.
    ie: 2 second ago, 5 minuites ago...etc
    '''
    now = datetime.datetime.now()    
    now = now.replace(tzinfo=None)
    d = d.replace(tzinfo=None)
    diff = now - d
    
    s = diff.seconds
    if diff.days > 2 or diff.days < 0:
        return d.strftime(default)
    elif diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '%s days ago' % diff.days
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '%s sec ago' % s
    elif s < 120:
        return '1 min ago'
    elif s < 3600:
        return '%s min ago' % (s/60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '%s hours ago' % (s/3600)    