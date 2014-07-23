'''
List of show constants, provide configuration relating to clip database. 
This file should how no dependencies and can be imported hassle free.

Sources values from the environment. 
'''
import os

show_name       = os.environ.get('PROD', 'tlp')
show_fps        = int ( os.environ.get('FILM_FPS', '24') )

show_width  = 1920
show_height = 1080

playblast_width  = 1920
playblast_height = 1080

# for published movies
preview_movie_width  = 1920
preview_movie_height = 1080

MOVIE_LIST = ['avi', 'mp4', 'mov', 'mpeg', 'mpg']

LOGGER = None

def get_logger():
    global LOGGER
    
    if LOGGER==None:
        import logging       
    
        LOGGER = logging
    
    return LOGGER
