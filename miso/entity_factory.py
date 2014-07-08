'''
\namespace miso.entity_factory
 
 Entity factory manufactures all the entities such as Sequence, Shot, and Version. 
 
 Entities caters production data via:
  1. functions: sequence.list_shots(), shot.list_versions(), shot.get_task()
  2. attribute getters: shot.entity_code(), shot.entity_id() 

 Entities should not directly expose native database data. ( ex: asset_code, shot_id )
 Rather they are accessed via getter functions to be independent of how the underlying 
 production database structures.
   
'''

import collections, traceback, time, getpass
from datetime import datetime

from miso import *
from miso.config import get_logger

LOG = get_logger()

class Entity:
    '''
    The base class for wrapping production db data.
    This will be inherited by Shot, Sequence, Asset entities.
    This is an Abstract Class and should not be instantiated directly.
    '''
    def __init__(self, entity_type, entity_id, entity_code, entity_data):
        '''
        @param entity_type
        @param entity_id
        @param entity_code
        @param entity_data        
        '''
        self._entity_type   = entity_type
        self._entity_id     = entity_id
        self._entity_code   = entity_code
        self._entity_data   = entity_data
        
        self._entity_label  = None      
        self._project       = None  
        

    def entity_type(self):
        return self._entity_type

    def entity_id(self):
        return self._entity_id        
    
    def entity_code(self):
        return self._entity_code
    
    def entity_label(self):
        return self._entity_label
    
    def raw_entity_data(self):        
        return self._entity_data
    
    def set_label(self, value):
        self._entity_label = value        
        
    def set_project(self, project):
        self._project = project
        
    def project(self):
        '''
        @rtype : Project  
        '''
        return self._project            
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        
        elif ( self.entity_id() == other.entity_id() and
             self.entity_type() == other.entity_type() and
             self.project().entity_id() == other.project().entity_id() ):
            return True
        
        else:
            return False
            
    def __repr__(self):
        return "<Entity %s | code:%s | id: %s >" % (    
                                          self.entity_type(),
                                          self.entity_code(),
                                          self.entity_id(),
                                          )    

class Project(Entity):
    '''    
    Project is the root entity and holds direct reference to the prod_db plugin.  All object entities
    are created and cached through project entity via _objectfy_entity. 
     
    It's upto the plugin to conform the underlying production data into standard entities.
    
    The entity objects themselves will not directly access database fields. Rather the prod_db plugin will
    decorate it with data from database.
               
    Caching at this level ensures object is created once per entity.
    '''

    def __init__(self, prod_db):
        '''
        @param prod_db production database api.        
        '''        
        
        # get the show info from the production db.        
        self._prod_db = prod_db
        
        show_info = self._prod_db.get_show()
        
        Entity.__init__(self,   entity_type = ENT_PROJ, 
                                entity_id   = show_info['id'], 
                                entity_code = show_info['code'], 
                                entity_data = None)
        
        # the session user, responsible for write operations
        self.__session_user_code = None 
        
        self._entity_cache = {}
        

    def db_conn(self):
        '''
        @return the underlying datablase connection.
        '''
        return self._prod_db.db_conn()
        
    
    def db_access_metric(self):
        '''
        return any database access metrics since begging of session.
        @return db access metrics
        @rtype: dict
        '''
        return self._prod_db.db_access_metric()
    
    
    def _objectfy_entity(self, entity_type, entity_id, entity_data=None):        
        '''
        Does two things:
        1) Call on the prod_db plugin to convert the query data into an object 
        using entity data and entity class.  The plugin will decorate the entity object.
        
        2) Cached the data using entity_type, entity_id pair
        @param entity_type
        @param entity_id
        @param entity_data The data retrieve from the prod db.
        @param entity_class The entity object class, used by prod db to construct object.
        @return the entity object.
        '''
        ent_map = {   
                ENT_SEQ:        Sequence,                        
                ENT_SHOT:       Shot,
             
                ENT_ASSET:      Asset,
                
                ENT_TASK:       Task,
                ENT_USER:       User,
                
                ENT_VERSION:    Version,
                ENT_TASK_TYPE:  TaskType,
                
                }        
        
        if entity_type not in self._entity_cache:
            self._entity_cache[entity_type] = {}

        obj = None
        
        if entity_id not in self._entity_cache[entity_type]:
            # Ask prod db to instantiate the object and decorate it with prod_db information
            try:
                if not entity_data:
                    LOG.warning("Failed to create entity with NULL data for entity type '%s' : entity_id '%s'" %   
                                                                                (entity_type, entity_id))                    
                else:
                    obj = self._prod_db.objectfy_entity(  entity_class = ent_map[entity_type], 
                                                          entity_type  = entity_type,
                                                          entity_id    = entity_id,
                                                          entity_data  = entity_data)
            except ObjectfyEntityError, e:
                LOG.warning("Failed to create entity from data entity type '%s' : entity_id '%s' with data %s." %  
                                                                                (entity_type, entity_id, entity_data))
                
                
                LOG.warning( traceback.format_exc() )
                                                                      
            if obj:                                    
                self._entity_cache[entity_type][entity_id] = obj            
                # decorate the object with the top project object.
                obj.set_project(self)
        else:
            obj = self._entity_cache[entity_type][entity_id]        
        
        return obj
    
    
    def _find_cached_entity(self, entity_type, entity_code=None, entity_id=None):
        '''
        Find the cached entity by entity code (slower) or by entity id (faster).
        
        Entities are cached by entity_id and not entity code, since entity code is not required to be unique
         
        this will search and return all the objects that matches the entity_code/entity_id.
        
        @param entity_type
        @param entity_code
        @param entity_id
        @return the cached entity
        '''        
        result = []
        
        if entity_type in self._entity_cache:
            if entity_id!=None and entity_id in self._entity_cache[entity_type]:
                result = [ self._entity_cache[entity_type][entity_id] ]                
                
            elif entity_code!=None:            
                result = [ ent for ent in self._entity_cache[entity_type].values() if ent.entity_code()==entity_code ]
        
        return result
    
    
    def clear_cache(self):
        '''
        Purge the cached entity objects.
        '''
        self._entity_cache = {}        
    

    def list_sequences(self):
        '''
        @rtype: [ Sequence ]
        '''
        seq_list = []
        
        for seq_id, seq_data in self._prod_db.list_sequences():
            obj = self._objectfy_entity( entity_type     = ENT_SEQ, 
                                         entity_id       = seq_id, 
                                         entity_data     = seq_data                                        
                                       )  
            if obj:          
                seq_list.append(obj)
            
        seq_list.sort( lambda x,y: cmp(x.entity_code(), y.entity_code())  )
            
        return seq_list   
        
    
    def sequence (self, seq_code=None, seq_id=None ):
        '''
        Get the sequence object, either by code or by id.
        @param seq_code
        @param seq_id
        @return the matching seq object
        @rtype: Sequence
        '''
        
        # attempt to find in cache entity object
        seq_obj_search = self._find_cached_entity( ENT_SEQ, seq_code, seq_id )        
        
        if seq_obj_search:
            seq_obj = seq_obj_search[0]
        
        # not cached, make entity.
        else:        
            seq_id, seq_data = self._prod_db.get_sequence(seq_code, seq_id)
            
            seq_obj = self._objectfy_entity(  entity_type     = ENT_SEQ, 
                                              entity_id       = seq_id, 
                                              entity_data     = seq_data,                                              
                                             )            
        
        return seq_obj
    

    
    def shot(self, shot_code=None, shot_id=None, seq_id=None):
        '''
        Get the shot either by shot code or shot id
        @param shot_code
        @param shot_id
        @return the matching shot object
        @rtype: Shot
        '''
        
        # attempt to find in cache entity object
        shot_obj_search = self._find_cached_entity( ENT_SHOT, shot_code, shot_id )

        if shot_obj_search:
            shot_obj = shot_obj_search[0]
        
        # not cached, make entity
        else:        
            shot_id, shot_data = self._prod_db.get_shot(shot_code, shot_id, seq_id)
            
            shot_obj = self._objectfy_entity( entity_type     = ENT_SHOT, 
                                              entity_id       = shot_id, 
                                              entity_data     = shot_data,                                              
                                            )        
         
        return shot_obj
    
    
    
    def get_version(self, ver_id):
        '''
        Get the shot either by shot code or shot id
        @param shot_code
        @param shot_id
        @return the matching shot object
        @rtype: Version
        '''
        
        # attempt to find in cache entity object
        ent_search = self._find_cached_entity( ENT_VERSION, entity_id=ver_id )

        if ent_search:
            assert ent_search[0]!=None
            return ent_search[0]
        
        # not cached, make entity
        else:        
            raise NotImplementedError       
    
    
    
    def get_shot_audio(self, shot_entity):
        return self._prod_db.get_shot_audio(shot_entity)
       
    
    def list_shots (self, sequence='all'):
        '''
        @param sequence [optional - default 'all'] return shots by sequence_code, else by default will return all the shots.
        @rtype: [ Shot ]
        '''
        assert sequence!=None, "Failed to list shot, no sequence provided."
        
        shot_list = []
        
        if isinstance(sequence, basestring):
            if sequence=='all':
                seq_obj = 'all'
            else:
                seq_obj = self.sequence(sequence)
        else:
            seq_obj = sequence  
        
        for shot_id, shot_data in self._prod_db.list_shots( seq_obj ):
            obj = self._objectfy_entity( entity_type     = ENT_SHOT, 
                                         entity_id       = shot_id, 
                                         entity_data     = shot_data,
                                          
                                       )            
            if obj:
                shot_list.append(obj)
            
            
        shot_list.sort( lambda x,y: cmp(x.entity_code(), y.entity_code())  )
            
        return shot_list
         
    
    def get_entity_from_meta(self, entity_meta):
        '''
        Return the entity, given the meta.  ie: {'entity_type':ENT_SHOT, 'id':5}
        @rtype: Entity
        '''
        if entity_meta==None:
            return None
        
        if entity_meta['entity_type'] == ENT_SHOT:
            return self.shot(shot_id=entity_meta['id'] )
        
        elif entity_meta['entity_type'] == ENT_ASSET:
            return self.asset(asset_id=entity_meta['id'] )   
             
        elif entity_meta['entity_type'] == ENT_SEQ:
            return self.sequence(seq_id=entity_meta['id'] )         

        elif entity_meta['entity_type'] == ENT_PROJ:
            return self
        
        else:
            LOG.warning("Can not resolve entity from meta: %s" % entity_meta)          
    
    def list_assets(self, asset_type):
        '''
        @param asset_type [ str, list ] one or more of ENT_CHAR, ENT_PROP, ENT_SET, ENT_VEHICLE  
        @return the list of asset objects of the asset_type from the project.
        @rtype: [ Asset ]
        '''        
        if type(asset_type) in (str, unicode):
            asset_entity_type_list = [asset_type]
        elif type(asset_type) in (list, tuple):
            asset_entity_type_list = asset_type
        
        asset_list = []
        
        for asset_type in asset_entity_type_list:
            _asset_list = []
            
            for asset_id, asset_data in self._prod_db.list_assets( asset_type ):
                obj = self._objectfy_entity( entity_type     = ENT_ASSET, 
                                             entity_id       = asset_id, 
                                             entity_data     = asset_data,                                         
                                           )
                if obj:   
                    _asset_list.append(obj)            
            
            _asset_list.sort( lambda x,y: cmp(x.entity_code(), y.entity_code())  )
                
            asset_list += _asset_list
            
        return asset_list
         
        
    
    def asset(self, asset_code=None, asset_type=None, asset_id=None):
        '''
        @param asset_type one of ENT_CHAR, ENT_PROP, ENT_SET
        @return the asset object
        @rtype: Entity
        '''
        # attempt to find in cache entity object
        asset_obj_search = self._find_cached_entity( ENT_ASSET, asset_code, asset_id )        
        
        if asset_obj_search:
            asset_obj = asset_obj_search[0]
        
        # not cached, manufacture one.    
        else:        
            asset_id, asset_data = self._prod_db.get_asset( asset_code = asset_code, 
                                                            asset_id   = asset_id,
                                                            asset_type = asset_type
                                                            )
            
            asset_obj = self._objectfy_entity(   entity_type     = ENT_ASSET, 
                                                 entity_id       = asset_id, 
                                                 entity_data     = asset_data                                                 
                                                )         
        return asset_obj
    
    
    
    def set_session_user(self, user):
        '''
        set the session user, which will be responsible for all the write operations to database.
        @param user the login name
        '''
        self.__session_user_code = user
        
        
    def get_session_user(self):
        '''
        @return the session user
        '''
        if self.__session_user_code == None:
            self.__session_user_code = getpass.getuser()
        
        
        return self.get_user( self.__session_user_code )
    
    
    def get_user(self, user):
        '''
        @type status: string 
        @param user either the user code or the user id
        @return the status object, given the id
        '''
         
        user_data = self._prod_db.get_user(user)
 
        user_obj  = self._objectfy_entity(       entity_type     = ENT_USER, 
                                                 entity_id       = user_data['id'], 
                                                 entity_data     = user_data                                                     
                                            )   
     
        return user_obj
        
    
    def get_task(self, task_id):
        '''
        @param task_id
        @return the task object, given the id
        '''
        # attempt to find in cache entity object
        task_obj_search = self._find_cached_entity( ENT_TASK, entity_id = task_id )              
        
        if task_obj_search:
            task_obj = task_obj_search[0]
         
        # not cached, manufacture one.    
        else:  
            _task_id, task_data = self._prod_db.get_task(task_id)
                   
            task_obj  =  self._objectfy_entity(          entity_type     = ENT_TASK, 
                                                         entity_id       = task_id, 
                                                         entity_data     = task_data,                                                         
                                                        )            

        return task_obj
    
    
    def get_task_type(self, task_type_id):
        '''
        return a list of task types
        '''
        task_type_obj  =  self._objectfy_entity(         entity_type     = ENT_TASK_TYPE, 
                                                         entity_id       = task_type_id, 
                                                         entity_data     = self._prod_db.get_task_type(task_type_id),                                                         
                                                        )         
        
        return task_type_obj
    
    
    def get_source_path(self, version):
        '''
        @return the source path of thev version
        '''
        return self._prod_db.get_source_path( version )
        
    
    def list_task_types(self, entity_type=None):
        '''
        @return the list of task types
        '''
        assert entity_type in (ENT_SHOT, ENT_ASSET)
        result = []
                
        for tt_id, tt_data in self._prod_db.list_task_types(entity_type):
            obj = self._objectfy_entity(    entity_type     = ENT_TASK_TYPE, 
                                            entity_id       = tt_id, 
                                            entity_data     = tt_data                                            
                                           )
            result.append(obj)
        
        return result
    
    
    def list_submission_types(self):
        '''
        @return list of the submission types
        '''
        return self._prod_db.list_submission_types()
        
        
    def list_status_types(self):
        '''
        @return list of all the possible status
        '''
        result = []
        
        for tt_id, tt_data in self._prod_db.list_status_types():
            obj = self._objectfy_entity(    entity_type     = ENT_STATUS, 
                                            entity_id       = tt_id, 
                                            entity_data     = tt_data                                            
                                           )
            result.append(obj)
            
        return result
        
    
    def list_tasks( self, entity_type=None, entity_id=None, task_id=None ):
        '''
        Retrieve the tasks for an entity, or tasks that match the task_id(s)
        @param entity_type
        @param entity_id
        @param task_id can be a list
        @return  a list of task, or a hash of task group by department.        
        '''
                    
        task_list = []      
        
        for task_id, task_data in self._prod_db.list_tasks( entity_type, entity_id, task_id ):
            obj = self._objectfy_entity(    entity_type     = ENT_TASK, 
                                            entity_id       = task_id, 
                                            entity_data     = task_data                                        
                                           )
            if obj:
                task_list.append(obj)
        
        return task_list    
    
    
    def list_clips(self,        entity_meta_list   = None,                       
                                task_type_code     = None,
                                 
                                artist             = None,
                                start_time         = None,
                                end_time           = None,  
                                                              
                                latest_only        = False, 
                                for_review_only    = False,
                                
                                query_entity_limit = 111,
                                query_version_limit = 1000 ):
        
        version_type = ['playblast','nuke_render','turntable','occlusion']
        self.list_versions(entity_meta_list, task_type_code, artist, start_time, end_time, version_type, latest_only, for_review_only, query_entity_limit, query_version_limit)
        
    
    
    
    def list_versions(self,     entity_list        = None,
                                entity_meta_list   = None,                       
                                task_type_code     = None,
                                 
                                artist             = None,
                                start_time         = None,
                                end_time           = None, 
                                
                                version_type       = None, 
                                                              
                                latest_only        = False, 
                                for_review_only    = False,
                                
                                query_entity_limit = 111,
                                query_version_limit = 1000 ):
        '''
        List all the versions attached to the entity.
        @param entity_list list of entities for which to query versions
        @param entity_meta_list list of entity meta dictionary ex:[ {'entity_type':ENT_SHOT, 'id':5 },...]
        @param start_time local time, either datetime object or seconds since Epoch  
        @param end_time local time, either datetime object or seconds since Epoch        
        @param task_type_code [optional str or list] filter the version to the related task
        @param latest_only [optional] only return the latest version
        @param for_review_only [optional] only return the version marked for review.
        @param query_entity_limit [optional, default=111] The limit on the entity query
    
        @return all the version that matches the criteria
        @rtype: VersionResult   
        '''
        ver_list = []
        
        list_ver_func = self._prod_db.list_versions_latest if latest_only else self._prod_db.list_versions
        
        if type(entity_list) in (list, tuple):
            entity_meta_list = [ {'entity_type':e.entity_type(), 'id':e.entity_id() } for e in entity_list ]
        elif hasattr( entity_list, 'entity_type'):
            entity_meta_list = [ {'entity_type':entity_list.entity_type(), 'id':entity_list.entity_id() } ]
         
        if type(start_time)==datetime:
            start_time = int(start_time.strftime("%s"))
            
        elif type(start_time) in (str, unicode):
            start_time = int( round( float(start_time) )  )            
        
        if type(end_time)==datetime:
            end_time = int(end_time.strftime("%s"))
            
        elif type(start_time) in (str, unicode):
            end_time = int( round( float(end_time) )  )
            

        for version_id, version_data in list_ver_func( entity_meta_list   = entity_meta_list, 
                                                       task_type_code     = task_type_code,
                                                       
                                                       artist             = artist,
                                                       start_time         = start_time,
                                                       end_time           = end_time,  
                                                       
                                                       version_type       = version_type,                                                                                                              

                                                       ent_limit          = query_entity_limit,
                                                       ver_limit          = query_version_limit ):
            
            obj = self._objectfy_entity(    entity_type     = ENT_VERSION, 
                                            entity_id       = version_id, 
                                            entity_data     = version_data                                            
                                           )
            if obj:
                ver_list.append(obj)
        
        return VersionResult(self, ver_list)  
    
    
    def list_clips_from_versions(self, version_list ):
        '''
        @param version        
        @return clips group by submit type, and version id
        @rtype: ClipResult 
        '''
        clip_list = []
        
        # version_id_to_ver_hash = dict( [(ver.entity_id(), ver) for ver in version_list ] )        
        
        result =  self._prod_db.list_clips_from_versions( version_list )
        
        for clip_id, clip_data in result:
            clip_list.append (
                              self._objectfy_entity(   entity_type      = ENT_VIDEO_CLIP,
                                                        entity_id       = clip_id, 
                                                        entity_data     = clip_data                                            
                                                       )                              
                              )
             
        return ClipResult(clip_list)
    

    def create_version(self, task, source_path, comment, artist=None, date=None):        
        '''
        @param task
        @type task: Task
        @param source_path
        @param comment
        @param artist
        @param date
        @return Version
        @rtype: Version
        '''
        if date==None:
            date    = time.time() 
            
        if artist==None:
            artist  = getpass.getuser()
        
        
        pre_ver = task.latest_version()
            
        success = self._prod_db.create_version(task, source_path, comment, artist, date )        
        
        assert success, "Failed to create version." 
        
        new_ver = task.latest_version()        
        
        
        if pre_ver==None:
            expected_next_num = 1
        else:
            expected_next_num = pre_ver.number() + 1
            
        assert new_ver.number()==expected_next_num, \
                "Error: expected new version to be %s, got %s." %(
                                                                  expected_next_num,                                                                                                      
                                                                  new_ver.number()
                                                                  )
        
        return new_ver
    
    
    def create_frame_submission(self,
                                                                
                                version_entity,
                                 
                                source_path, 
                                preview_path,
                                
                                start_frame = None, 
                                end_frame   = None,
                                
                                tags        = [],
                                
                                submit_type = None, 
                                file_type   = None,                                 
                                ):
        '''
        @param version_entity
        @param source_path
        @param preview_path
        @param start_frame
        @param end_frame
        @param tags
        @param submit_type one of ['playblast','occlusion_playblast','render']
        @param file_type one of ['movie','sequence','image']      
        '''
        
        if submit_type==None:
            submit_type = "playblast"
            
        assert submit_type in ['playblast','occlusion_playblast','render'], \
                                "You must specify the file type to be one of %s, you gave %s." % (
                                                                str(['playblast','occlusion_playblast','render']),
                                                                file_type
                                                                )
            
        success, fsubmit_id = self._prod_db.create_frame_submission(
                                                version_entity, 
                                                source_path, 
                                                preview_path,
                                                
                                                start_frame     = start_frame, 
                                                end_frame       = end_frame,
                                                
                                                tags            = tags,
                                                
                                                submit_type     = submit_type, 
                                                file_type       = file_type                                         
                                              )
        
        assert success, "Failed to create version." 
        
        # get the new clip
        result = self.list_clips_from_versions( [version_entity] )
        
        match_clip = result.filter(submit_type=submit_type )
        
        if type(match_clip) in (list, tuple):  # this is unexpected, since there should only be one type of submit_type per version
            LOG.warning("Unexpected, found '%s' clips of submit_type '%s' for version '%s'  " % ( 
                                            len(match_clip), submit_type, version_entity ) )
            
            return [ c for c in match_clip if c.publish_entity().entity_id() ==  fsubmit_id ][0] 
        
        else:
            return match_clip
        
    
    def set_task_status(self, task, status, tech=False):
        '''
        Set the task status to status
        @param task task object
        @param status, either the status id or status object.
        @param tech is technical status or not, default: normal status.
        '''
        try:
            self._prod_db.set_task_status( task_id    = task.entity_id(),                                       
                                           status_id  = status.entity_id(),
                                           
                                           user_id    = self.get_session_user().entity_id(),
                                                                                  
                                           tech       = tech
                                          )
        except:
            LOG.critical("Error setting status.")
        

    def batch_list_entities(self, entity_code_list=None, entity_id_list=None, search_query=None ):
        '''
        batch get the entities
        @param entity_code can be list
        @param entity_id can be list
        @param search_query query regular expression ex: 'sc0120', 'bike', '^bike[0-9]'        
        '''
        asset_list = []
        
        if search_query:
            assert  entity_code_list==None and entity_id_list==None, \
                        "To use search_query, do not supply parameter for entity_code_list nor entity_id_list."
        
        for entity_type, entity_id, entity_data in self._prod_db.batch_list_entities(entity_code  = entity_code_list, 
                                                                                    entity_id    = entity_id_list, 
                                                                                    search_query = search_query):
            obj = self._objectfy_entity( entity_type     = entity_type, 
                                         entity_id       = entity_id, 
                                         entity_data     = entity_data                                         
                                       )
            if obj:   
                asset_list.append(obj)        
        
        if entity_code_list:
            asset_list.sort( lambda x,y: cmp(  entity_code_list.index( x.entity_code() ), entity_code_list.index(y.entity_code())  )  )
            
        elif entity_id_list:
            asset_list.sort( lambda x,y: cmp(  entity_id_list.index( x.entity_id() ), entity_id_list.index(y.entity_id())  )  )
        
        else:
            asset_list.sort( lambda x,y: cmp( x.entity_code(), y.entity_code() )  )
            
        return asset_list
        
        
class Sequence(Entity):    
    def __init__(self, entity_id, entity_code, entity_data):
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data, 
                        entity_type = ENT_SEQ,                         
                        )
    

    def list_shots(self):
        return self.project().list_shots( self )
        
        
    def shot(self, shot_code=None, shot_id=None):
        '''
        @rtype: Shot
        '''
        return self.project().shot(shot_code, shot_id, self.entity_id())

    
class Shot(Entity):    
    def __init__(self, entity_id, entity_code, entity_data, edit_in=None, edit_out=None, 
                 seq_order=None, parent_seq_id=None):
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data,
                        entity_type = ENT_SHOT
                        )    
        
        self._edit_in       = edit_in
        self._edit_out      = edit_out
        self._seq_order     = seq_order
        self._parent_seq_id = parent_seq_id
    
    def sequence(self):
        '''
        @return the parent sequence entity.
        '''
        return self.project().sequence(seq_id=self._parent_seq_id)        
    
    def edit_cut(self):
        '''
        @return the edit in and out tuple
        '''
        return self._edit_in, self._edit_out

    
    
    def list_tasks(self):
        '''
        @return the list of task entities associated with shot
        @rtype [ Tasks ] 
        '''
        task_list = self.project().list_tasks(self.entity_type(), self.entity_id() )

        return task_list
    
    
    def list_versions(self, task_type_code=None, latest_only=False, for_review_only=False):
        '''
        @return the list of versions 
        @rtype: VersionResult  
        '''
        return self.project().list_versions(entity_meta_list = [{'entity_type':ENT_SHOT,
                                                                 'id':self.entity_id()}], 
                                            latest_only = latest_only, 
                                            task_type_code = task_type_code,
                                            for_review_only = for_review_only )
    
    def prev_shot(self):
        '''
        @return the previous shot
        @rtype: Shot
        '''
        
        return self.project().shot( shot_id = self._prev_shot_id ) if self._prev_shot_id else None
    
    
    def next_shot(self):
        '''
        @return the previous shot
        @rtype: Shot
        '''
        return self.project().shot( shot_id = self._next_shot_id ) if self._next_shot_id else None
    
    
    def task(self, task_code):
        '''
        @param task_code
        @return the task attached to the shot with the task code.  ex: "edt", "anf"
        @rtype: Task 
        '''
        task_search = [ t for t in self.list_tasks() if t.entity_code() == task_code ]
        
        if task_search:
            return task_search[0]  
        else:
            raise TaskNotFoundError, "Entity '%s' doesn't have task '%s'." % (self.entity_code(), task_code)
    
        
        
    def list_parents(self, entity_type=None):
        '''
        @param entity_type Filter the entity by type, ex: ENT_SHOT
        '''
        return self.project().list_asset_parents(self, entity_type)
    
    
    def list_children(self, entity_type=None):
        '''
        @param entity_type Filter the entity by type, ex: ENT_SHOT
        '''
        return self.project().list_asset_children(self, entity_type)    
    
    
    def audio(self):
        '''
        @return the audio for the shot
        @rtype str
        '''
        return self.project().get_shot_audio(self)
        

        
class Asset(Entity):
    '''
    Stores the character, prop, set. 
    '''    
    def __init__(self, entity_id, entity_code, entity_data, asset_type, asset_label=None):
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data, 
                        entity_type = ENT_ASSET                        
                        )
        
        self._asset_type = asset_type
        self.set_label(asset_label)
    
    def asset_type(self):
        return self._asset_type
    

    def list_tasks(self):
        task_list = self.project().list_tasks(self.entity_type(), self.entity_id() )
        
        return task_list
    
    
    def task(self, task_code):
        '''
        @param task_code
        @return the task attached to the asset with the task code.  ex: "edt", "anf" 
        @rtype Task
        '''
        task_search = [ t for t in self.list_tasks() if t.entity_code() == task_code ]
        
        if task_search:
            return task_search[0]    

        
class Task(Entity):    
    def __init__(self, entity_id, entity_code, entity_data, parent_entity_meta, department_meta,
                       artist_meta  ):
        
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data,
                        entity_type = ENT_TASK                        
                        )
        

        self._department            = department_meta
        self._parent_entity_meta    = parent_entity_meta
        self._artist_meta           = artist_meta
        
    
    def artist(self, as_string=True):
        '''
        @param as_obj return user as an object.
        '''
        if as_string:
            return self._artist
        else:
            return self.project().get_user(self._artist)           
                
    def status(self):
        return self.project().get_status( self._task_status_id )
    
        
    def set_status(self, value):
        '''        
        @param value can be the status id or status code
        '''        
        status = self.project().get_status(value)
        self._task_status_id = status.entity_id()
        
        self.project().set_task_status( self, status )
    
    
    def task_type(self):
        return self.project().get_task_type( self )
                
        
    def set_tech_status(self, value):
        '''        
        @param value can be the status id or status code
        '''        
        status = self.project().get_status(value)
        self._task_tech_status_id = status.entity_id()
        
        self.project().set_task_status( self, status, tech=True )
        
        
    def label(self):
        return self._task_label
    
        
    def set_label(self, value):
        self._task_label = value
        
        
    def list_versions(self, latest_only=False, for_review_only=False):
        '''
        List the versions related to the task
        @param latest_only only return the latest version
        @param for_review_only filter by versions marked for review
        @return version entities in a list.
        @rtype: VersionResult
        '''        
        return self.project().list_versions(     entity_meta_list = [
                                                        {'entity_type':self.parent_entity().entity_type(),
                                                         'id':self.parent_entity().entity_id()}],
                                                 task_type_code  = self.entity_code(),
                                                 latest_only     = latest_only, 
                                                 for_review_only = for_review_only )
        
        
    def latest_version(self, for_review_only=False):
        '''
        @param for_review_only filter versions marked for review
        @return the latest version
        @rtype: Version
        '''
        result = self.list_versions(latest_only=True, for_review_only=for_review_only)
        
        if result:
            return result[0]
    
    
    def create_version(self, source_path, comment="hello, world", return_publisher=False):
        '''
        @param source_path path to the file or folder to be published. 
        @return version
        @rtype: Version
        '''
        # allocate a version in database, if possible set to be inactive
        # publish the file, or return publish object.
        # publisher object set active.
        
        return self.project().create_version(     task = self, 
                                                  source_path = source_path, 
                                                  comment = comment
                                                  )
     
    def parent_entity(self):
        return self.project().get_entity_from_meta( self._parent_entity_meta  )
    

class TaskType(Entity):
    def __init__(self, entity_id, entity_code, entity_data, label, colour, department):
        Entity.__init__(self, 
                    entity_id   = entity_id, 
                    entity_code = entity_code,
                    entity_data = entity_data,
                    entity_type = ENT_TASK_TYPE                                      
                    )
        
        self._label      = label
        self._department = department 
        self._colour     = colour
    
    def name(self):
        return self.entity_code() 
    
    def label(self):
        return self._label
    
    def colour(self):
        return self._colour

    def department(self):
        return self._department
    


class ClipResult(collections.Iterator):
    def __init__(self, result):
        
        self._clip_list = []
                
        for clip in result:           
            self._clip_list.append( {
                                        'entity_code':  clip.publish_entity().parent_version().asset().entity_code(),
                                        'task_code':    clip.publish_entity().parent_version().task_code(),
                                        'ver_number':   clip.publish_entity().parent_version().number(),
                                        'submit_type':  clip.publish_entity().submit_type(),
                                        'clip':         clip                                                      
                                     }
                                   )
            
    def __len__(self):
        return len(self._clip_list)

    def __getitem__(self, key):
        assert type(key)==int, "Clip Result index must be an integer, given %s" % key
        
        return self._clip_list[key]['clip']

    def __iter__(self):
        self._index = -1
        return self
        
    def next(self):
        if self._index >= (len(self._clip_list)-1):
            raise StopIteration
        else:
            self._index += 1            
            return self._clip_list[self._index]['clip']
                    
    
    def list_assets(self):
        return self.list_entities()
    
    def list_entities(self):
        return list(set( [ c['entity_code'] for c in self._clip_list ] ))
    
    def list_tasks(self):
        return list(set( [ c['task_code'] for c in self._clip_list ] ))
    
    def list_versions(self):
        return list(set( [ c['ver_number'] for c in self._clip_list ] ))

    def list_submit_types(self):
        return list(set( [ c['submit_type'] for c in self._clip_list ] ))

            
    def filter(self, entity_code=None, task_code=None, version_num=None, submit_type=None):
        '''
        @param entity_code
        @parrm task_code
        @param version_num
        @param submit_type 
        @return a list of clips matching the criteria
        @rtype: clipbox.clip_source.ClipSource
        '''
        filter_list = [ c for c in self._clip_list ] 
        
        if entity_code:
            filter_list = [ c for c in filter_list if c['entity_code']==entity_code ]
            
        if task_code:
            filter_list = [ c for c in filter_list if c['task_code']==task_code ]
             
        if version_num:
            filter_list = [ c for c in filter_list if c['version_num']==version_num ]
            
        if submit_type:
            filter_list = [ c for c in filter_list if c['submit_type']==submit_type ]
            
        if len(filter_list)==0:
            return None
        
        elif len(filter_list)==1:
            return filter_list[0]['clip']
        
        else:
            return [ f['clip'] for f in filter_list ]


    def __repr__(self):
        return "<Clip query results | %s entries>" % len(self._clip_list)     


class VersionResult(collections.Iterator):
    def __init__(self, project, result):
        '''
        @param project
        @type project: Project 
        
        '''
        
        self._ver_list  = []
        self._project   = project 
        
        # batch cache the task
        task_id_list = [ ver._task_meta['id'] for ver in result if ver._task_meta ]
        if task_id_list:
            self._project.list_tasks(task_id = task_id_list)
        
        for ver in result:
            try: 
                task = ver.task()
                entity = ver.parent()
                
                self._ver_list.append( {
                                        'entity_code':  entity.entity_code() if entity else None,
                                        'task_code':    task.entity_code() if task else None,
                                        'ver_number':   ver.number(),
                                        'artist':       ver.artist(),
                                        'ver':          ver                                              
                                     }
                                   )
            except:
                LOG.critical("Can not resolve version entity from data %s." % ver, exc_info=1)

    def __len__(self):
        return len(self._ver_list)                
            
    def __iter__(self):
        self._index = -1
        return self
    
    def __getitem__(self, key):
        assert type(key)==int, "Version Result index must be an integer, given %s" % key
        
        return self._ver_list[key]['ver']    
        
    def next(self):
        if self._index >= (len(self._ver_list)-1):
            raise StopIteration
        else:
            self._index += 1            
            return self._ver_list[self._index]['ver']          

    def list_artists(self):
        return list(set( [ c['artist'] for c in self._ver_list ] ))            

    def list_entities(self):
        return list(set( [ c['entity_code'] for c in self._ver_list ] ))
    
    def list_tasks(self):
        result = list(set( [ c['task_code'] for c in self._ver_list ] ))
        result.sort()
        
        return result
    
    def list_versions(self):
        return list(set( [ c['ver_number'] for c in self._ver_list ] ))

            
    def filter(self, entity_code=None, task_code=None, version=None ):
        '''
        @param entity_code
        @parrm task_code
        @param version_num
        @return a list of clips matching the criteria
        @rtype: Version
        '''
        filter_list = [ c for c in self._ver_list ] 
        
        if entity_code:
            filter_list = [ c for c in filter_list if c['entity_code']==entity_code ]
            
        if task_code:
            filter_list = [ c for c in filter_list if c['task_code']==task_code ]
             
        if version:
            filter_list = [ c for c in filter_list if c['ver_number']==version ]
            
        if len(filter_list)==0:
            return None
        
        return [ f['ver'] for f in filter_list ] 
        
        
    def __repr__(self):
        return "<Version query results | %s entries>" % len(self._ver_list)            
           
 
class FrameSubmission(Entity):
    def __init__(self, entity_id, entity_code, entity_data, 
                 preview_path, source_path,
                 parent_version_id, publish_date, 
                 submit_type, file_type, tags ):
        '''
        @param submit_type one of  ['playblast', 'occlusion_playblast','render','turntable']
        @param file_type one of ['video','image','sequence']
        @param tags list of strings
        '''
         
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data, 
                        entity_type = ENT_VIDEO_CLIP
                        )
 
        self._submit_type = submit_type
        self._preview_path  = preview_path
        self._source_path   = source_path
         
        self._parent_version_id = parent_version_id         
        self._publish_date = publish_date
        
        self._file_type    = file_type
        self._submit_type  = submit_type
        self._tags         = tags        
        
    
    def __repr__(self):
        ver = self.parent_version()
        return "<Frame submit Entity | submit_type: %s | code:%s | task:%s | ver:%s >" % (
                                                                      self._submit_type,    
                                                                      ver.entity_code(),
                                                                      ver.task_code(), 
                                                                      ver.number() )
             
    def parent_version(self):
        '''
        Get the parent version of the clip
        '''
        return self.project().get_version( self._parent_version_id )
        
        
    def parent_version_id(self):
        '''
        @return the frame submission parent version. 
        '''
        return self._parent_version_id
     
     
    def submit_type(self):
        '''
        @return the submission type ['playblast', 'occlusion_playblast','render','turntable']
        '''
        return self._submit_type
     
     
    def tags(self):
        '''
        @return the tags
        '''
        return self._tags    
     
     
    def source_path(self, flg_stereo=False):        
        return self._clip_source.get_source_path(flg_stereo, source_preference="frames")
         
         
    def preview_path(self, flg_stereo=False):
        return self._clip_source.get_source_path(flg_stereo, source_preference="movie")
    

class User(Entity): 
    def __init__(self, entity_id, entity_code, entity_data, first_name, last_name):
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data, 
                        entity_type = ENT_USER,                         
                        )
        
        self._first_name = first_name
        self._last_name  = last_name
    
    def first_name(self):
        return self._first_name
    
    def last_name(self):
        return self._last_name

                
        
class Version(Entity):    
    def __init__(self,  entity_id, entity_code, entity_data,
                        version_num, artist, publish_date, description, status, for_review, 
                        task, department, parent_meta        
                        ):
        
        Entity.__init__(self, 
                        entity_id   = entity_id, 
                        entity_code = entity_code,
                        entity_data = entity_data, 
                        entity_type = ENT_VERSION
                        )
        
        self._version_num   = version_num
        self._artist        = artist
        self._publish_date  = publish_date
        self._status        = status
        self._description   = description
        self._for_review    = for_review
        
        self._task_meta     = task
        self._dept_meta     = department
        self._parent_meta   = parent_meta 
        
    def __repr__(self):
        related_task = self.task().entity_code() if self.task() else None
        return "<Version code:%s | id:%s | parent:%s | task:%s | ver:%s >" % (    
                                                                      self.entity_code(), 
                                                                      self.entity_id(), 
                                                                      self.parent(),
                                                                      related_task, 
                                                                      self.number() )
    
    def number(self):
        return self._version_num

    def version(self):
        return self.number()
    
    def task(self):
        if self._task_meta == None:
            return None
        else:
            return self.project().get_task( self._task_meta['id'] )
    
    def artist(self, as_string=True):
        '''
        @param as_obj return user as an object.
        '''
        if as_string:
            return self._artist
        else:
            return self.project().get_user(self._artist)
            
            
    def publish_date(self, as_string=False):
        if as_string:
            return time.strftime('%b/%d/%y %H:%M:%S %a', self._publish_date) 
        else:
            return self._publish_date
    
    def description(self):
        return self._description
    
    def comment(self):
        return self._description    
    
    def status(self):
        return self.project().get_status(self._status)
        
    def parent(self):
        return self.project().get_entity_from_meta(self._parent_meta)          

    def path(self):        
        return self.project().get_source_path(self)
    
    
    def list_video_clips(self):
        '''
        Return a list of clip source decorated with the frame submission entity
        @rtype: [ clipbox.clip_source.ClipSource ]
        '''
        return self.project().list_clips_from_versions( [self] )
    
    
    def for_review(self):
        '''
        Indicate if the item is for review or not.
        '''
        return self._for_review 
    
    
    def set_for_review(self, flg_for_review=True):
        '''
        Set the item for review or not
        '''
        self.project()._prod_db.set_version_for_review(self, flg_for_review)
        self._for_review = flg_for_review
                


    def create_frame_submission(    self,
                                     
                                    source_path, 
                                    preview_path,
                                    
                                    start_frame = None, 
                                    end_frame   = None,
                                    
                                    tags        = [],
                                    
                                    submit_type = None, 
                                    file_type   = None,                                 
                                    ):
        '''
        @param version_entity
        @param source_path
        @param preview_path
        @param start_frame
        @param end_frame
        @param tags
        @param submit_type one of ['playblast','occlusion_playblast','render']
        @param file_type one of ['movie','sequence','image']
        @return frame submission wrapped in clip source
        @rtype: clipbox.clip_source.ClipSource
        '''
        
        return self.project().create_frame_submission(
                                               
                                    version_entity  = self,                                     
                                    source_path     = source_path, 
                                    preview_path    = preview_path,
                                    
                                    start_frame = start_frame, 
                                    end_frame   = end_frame,
                                    
                                    tags        = tags,
                                    
                                    submit_type = submit_type, 
                                    file_type   = file_type,                                    
                                    )
        