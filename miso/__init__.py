'''
\namespace miso.entity_factory
 
 Entity factory manufactures all the entities such as Sequence, Shot, and Version. 
 
 Entities caters production data via:
  1. functions: sequence.list_shots(), shot.list_versions(), shot.get_task()
  2. attribute getters: shot.entity_code(), shot.entity_id() 

 Entities should not directly expose native database data. ( ex: asset_code, shot_id )
 Rather they are accessed via getter functions to be independent of how the underlying 
 production database structures.  
 
 Encapsulation done via the prod_db plugin
 
        ----------                  -------------------                 --------------------
        |  miso  |       <--+->     |  ftrack plugin  |       <--->     |    ftrack api    |    
        ----------          |       -------------------                 --------------------
                            |
                            |       -------------------                 -------------------
                            +->     | shotgun plugin  |       <--->     |   shotgun api   |
                                    -------------------                 -------------------
                                
         miso entities              plugin retrieve data                Different production database,
         with standard              from database and                   each with native way of  
         function and               construct miso entities.            storing data and raising
         attribute                  Also conform native exception       exceptions.
                                    and turn them into standard
                                    ones.  
 
 Example calls:  
 Hint: see unit test for more examples
 
        # connect to a TLP project 
        bbb = miso.project('bbb') 
        
        # list the sequence of bbb
        bbb.list_sequences() 
        
        # get sequence directly
        bunny_010 = bbb.sequence('bunny_010')
        
        # All entities are subclass of Entity, which uniquely identify the object within a project via: entity_type, entity_id
        # entities also have entity_code, while usually unique for most object, is not a requirement. 
        assert bunny_010.entity_type() == miso.ENT_SEQ
        assert bunny_010.entity_code() == "bunny_010"
        
        # list all the shots
        bunny_010.list_shots()
        
        # get shot from sequence
        bunny_010_0010 = bunny_010.shot('bunny_010_0010')
        
        # or get shot from project
        bunny_010_0010 = bbb.shot('bunny_010_0010')
        
        # get task
        bunny_010_0010.list_tasks()
        
        # list version from a shot
        bunny_010_0010.list_versions()
        
        # get version from a task
        bunny_010_0010.task('Anm').list_versions()
   
'''

import os, sys
import config

# entity enumerations
ENT_PROJ        = 'Proj'
ENT_SHOT        = 'Shot'
ENT_DEPT        = 'Department'

ENT_SEQ         = 'Sequence'
ENT_USER        = 'HumanUser'
ENT_TASK        = 'Task'

ENT_TASK_TYPE   = 'TaskType'
ENT_STATUS      = 'Status'
ENT_ASSET_TYPE  = 'EntityAssetType'

ENT_ASSET       = 'Asset'
ENT_CHAR        = 'Char'
ENT_PROP        = 'Prop'
ENT_SET         = 'Set'
ENT_FX          = 'FX'
ENT_VEHICLE     = 'Vehicle'

ENT_VERSION     = 'Version'     
ENT_VIDEO_CLIP  = 'Clip'


# store the connections to the project
_PROJ_SESSION = {}

def project(*arg_list, **arg_hash):
    return get_project ( *arg_list, **arg_hash )
    
    
def get_project(show=None, flg_dev=False):
    '''
    Create and maintain a project session.
    @param show name [optional] inherit from environment ex: APERO_PROJ
    @type show: str
    @param flg_dev [optional] connect to dev environment
    @type flg_dev: bool 
    @return a connection to the production database database
    @rtype: miso.entity_factory.Project 
    '''
    global _PROJ_SESSION
    
    if show==None:
        if config.show!=None:
            show = config.show
        else:
            raise IOError, "Failed to detect the show from the environment."
    
    session_key = (show, flg_dev)
    
    if not _PROJ_SESSION.has_key(session_key):
        _PROJ_SESSION[session_key] = _create_project_session(show, flg_dev)
    
    return _PROJ_SESSION[session_key]


def _create_project_session(show, flg_dev):
    '''
    Create a project session.  
    The project session with establish and maintain a connection to the prod db
    @param show
    @param flg_dev
    '''
    
    # establish a connection to the production database.
    dev_type     = 'dev' if flg_dev else 'prod'   
    prod_db_type = config.prod_db_conn_param[(show, dev_type)]['type']
    prod_db_conn = None

    if prod_db_type == 'shotgun':      
        from miso.pdb_plugins import shotgun_session            
        prod_db_conn = shotgun_session.ShotgunSession( config.prod_db_conn_param[(show, dev_type)] )
        
        import entity_factory
        return entity_factory.Project( prod_db_conn )
    
    
from exceptions import Exception

class ObjectfyEntityError(Exception):
    # failed to turn the meta data from production database into an entity objet.
    pass

class MisoError(Exception):
    # failed to turn the meta data from production database into an entity objet.
    pass

class TaskNotFoundError(MisoError):
    # failed to turn the meta data from production database into an entity objet.
    pass