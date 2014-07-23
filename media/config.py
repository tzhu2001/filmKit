import os

FF_ROOT = "/usr/bin"

RV_ROOT                 = os.environ.get("REZ_RV_ROOT", "/systeme/softs/rez/packages/rv/3.12.20")
RV_CONNECT_TIME_OUT     = 10

RV_DEFULT_CACHE_SETTING = True
RV_RAM = 4

DEBUG_LOG = True

PLAY_PREVIEW = False
PLAY_LEFT_EYE_ONLY = True

MOVIE_FORMATS = ['avi', 'mp4', 'mov', 'mpeg', 'mpg']
IMAGE_FORMATS = ["jpg", "png", "bmp", "tif", "jpeg", "tiff"]

DEFAULT_FPS = 24 

PLAY_ANNONTATE_META_HIDDEN_LIST=[]


LOGGER = None

def get_logger():
    global LOGGER
    
    if LOGGER==None:
        from pipeline.logger import log        
    
        LOGGER = log["media"]    
        LOGGER.setLevel(30)
    
    return LOGGER


