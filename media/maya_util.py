'''
Maya util is a collection of useful functions that is independent of show and company logic.  
'''
from maya import cmds, mel

import re

def get_scene_audio():
    '''    
    @return the active scene audio file and audio offset
    '''    
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider');
     
    audio_main =  cmds.timeControl(aPlayBackSliderPython, query=True, sound=True);
    if audio_main:
        audio_file_main = cmds.getAttr("%s.filename" % audio_main )
        audio_offset =  cmds.getAttr("%s.offset" % audio_main )                 
    
        return audio_file_main, audio_offset
    else:
        return '', 0