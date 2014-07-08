'''
\namespace miso.pdb_plugins.shotgun_session
 
 This is a plugin that conforms the bitro data into standard miso entities.

 ----------                  -------------------                 --------------------
 |  miso  |       <--+->     |  ftrack plugin  |       <--->     |   ftrack queries |    
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
                              
'''
import os, shutil, re, time, urllib, urllib2
from pprint import pformat, pprint
 
from shotgun_api3 import Shotgun

import miso
from miso import *

LOG = miso.config.get_logger()

# The Entity Types mapping to the Shotgun db table fields  
DB_FIELDS = { 
                ENT_PROJ:       ['id','sg_code','name'],                
                ENT_SHOT:       ['code', 'id', 'name', 'sg_sequence', 'project','cut_in','cut_out',
                                 'sg_cut_order'],
             
                ENT_SEQ:        ['code','id', 'cached_display_name', 'sg_status_list', 'project','sg_assigned_to', 'shots'], 
                
                ENT_TASK:       ['content','id','entity','sg_task_order','step','sg_status_list','task_assignees','due_date',
                                 'template_task','cached_display_name'],
             
                ENT_TASK_TYPE:  ['content','id','entity','sg_task_order','step','sg_status_list','project',
                                 'task_template.TaskTemplate.entity_type','cached_display_name', 'task_template'],
                
                ENT_ASSET:      ['code', 'id', 'cached_display_name', 'sg_status_list', 
                                 'description', 'sg_asset_type'],
                      
                ENT_VERSION:    ['code', 'id', 'sg_version_number', 'sg_version_type', 'description', 'created_at', 
                                 'created_by', 'sg_status_list','sg_path','sg_task','sg_task.Task.step','entity'],

              }


ENT_2_SG_TYPE = { ENT_SHOT: "Shot",   
                  ENT_ASSET:"Asset",  
                  ENT_SEQ:  "Sequence",
                  ENT_PROJ: "Project",
                }

SG_2_ENT_TYPE = dict( zip(ENT_2_SG_TYPE.values(), ENT_2_SG_TYPE.keys()))

   
class ShotgunSession:
    # some measure of how efficient shotgun has been used
    __db_access_metric = {}  
     
    def __init__(self, show, url, user, key ):
        '''
        @param show show name
        @param url db web url
        '''
        self._url   = url 
        self._user  = user
        self._key   = key

        self._sg = Shotgun(url, user, key)
         
        # cache project
        proj = self._find_one('Project', [('sg_code','is', show)], DB_FIELDS[ENT_PROJ] )
    
        self._show_id       = proj['id'] 
        self._show_code     = proj['sg_code'] 
        self._show_label    = proj['name']  
        
        self.__cached_tasks_types  = None 
        
    def db_conn(self):
        return self._sg
    
    def _sg_func(self, func, *arg_list, **arg_hash):
        LOG.debug("\n   <<< Calling Shotgun func '%s':" % func.__name__)
 
        LOG.debug(pformat(arg_list))
        LOG.debug(pformat(arg_hash))
        
        stime = time.time()
        
        result = func(*arg_list, **arg_hash)
        
        elapsed_time = (time.time()-stime)
        
        LOG.debug( "> Query Time: %s" % elapsed_time )
         
        if result:
            if type(result) in (tuple, list):
                LOG.debug( "\n>>> Result (first 1 of %s):" % len(result) )
                LOG.debug( pformat(result[0]) )
            else:
                LOG.debug( "\n>>> Result :" )
                LOG.debug( pformat(result) )                    
        else:
            LOG.warning("\n>>> Query with no result found.")
        
        if func.__name__ not in ShotgunSession.__db_access_metric:
            ShotgunSession.__db_access_metric[func.__name__] = {'call_count':1,
                                                     'time':elapsed_time}
        else:
            ShotgunSession.__db_access_metric[func.__name__]['call_count'] += 1
            ShotgunSession.__db_access_metric[func.__name__]['time'] += elapsed_time
            
        return result    
        
    
    def db_access_metric(self):
        '''
        @return db access metrics
        @rtype: dict
        '''
        return ShotgunSession.__db_access_metric
    
    
    def _find(self, *arg_list, **arg_hash):
        return self._sg_func( self._sg.find, *arg_list, **arg_hash )
    
        
    def _find_one(self, *arg_list, **arg_hash):
        return self._sg_func( self._sg.find_one, *arg_list, **arg_hash )
    
    
    def _summarize(self, *arg_list, **arg_hash):
        return self._sg_func( self._sg.summarize, *arg_list, **arg_hash )
    

    def resolve_sg_entity(self, entity):
        '''
        resolve shotgun entity to miso entity
        '''
        if entity:
            return { 
                     'entity_type': SG_2_ENT_TYPE[ entity['type'] ],
                     'id':          entity['id']
                    }
        else:
            return None
            
        
    def objectfy_entity(self, entity_class, entity_type, entity_id, entity_data):
        '''
        Create the entity class and decorated the class with bistro data.
        Conforming the data to standard of the object.
      
        '''          
        
        # instantiate the entity
        if entity_type in (ENT_SEQ):
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['code'],                              
                                 entity_data    = entity_data,
                                 )

        elif entity_type == ENT_SHOT:
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['code'],                              
                                 entity_data    = entity_data,
                                 
                                 edit_in        = entity_data['cut_in'],
                                 edit_out       = entity_data['cut_out'],
                                 
                                 seq_order      = entity_data['sg_cut_order'],
                                 parent_seq_id  = entity_data['sg_sequence']['id']
                                 )       
            
        elif entity_type == ENT_ASSET:
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['code'],                              
                                 entity_data    = entity_data,
                                 asset_type     = entity_data['sg_asset_type'],                                   
                                 )
            
        elif entity_type == ENT_TASK:          
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['content'],                              
                                 entity_data    = entity_data,
                                 
                                 parent_entity_meta = self.resolve_sg_entity(entity_data['entity']),
                                 
                                 artist_meta    = entity_data['task_assignees'],
                                 department_meta = entity_data['step'],
                                 )
            
        elif entity_type == ENT_USER:            
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['username'],                              
                                 entity_data    = entity_data,
                                 last_name      = entity_data['lastname'],
                                 first_name     = entity_data['firstname'],                                 
                                 )
                        
            
        elif entity_type == ENT_TASK_TYPE:
            # Note: in Shotgun there is no unique id for task type.
            # 
            ent = entity_class ( entity_id      = entity_data['content'],
                                 entity_code    = entity_data['content'],                              
                                 entity_data    = entity_data,
                                 colour         = None,
                                 label          = entity_data['cached_display_name'],
                                 department     = entity_data['step'],
                                 )
            
        elif entity_type == ENT_VERSION:
            if entity_data.get('sg_version_number')==None: # some version doesn't version number 
                ver_num = re.search('v([0-9]{2,4})', entity_data['code'])
                ver_num = int(ver_num.groups()[0]) if ver_num and ver_num.groups()[0].isdigit() else -1
            else:
                ver_num = entity_data.get('sg_version_number')
            
            if entity_data['entity']==None:
                LOG.warning('Version id=%s has no associated entity. Associate to project.' % entity_data['code'])
                entity_data['entity'] = {'entity_type':ENT_PROJ,'id':self._show_id}
                
            elif entity_data['entity']['type'] in SG_2_ENT_TYPE:
                entity_data['entity']['entity_type'] = SG_2_ENT_TYPE[ entity_data['entity']['type'] ]
            
            else:
                LOG.warning( "Can not map the version's (id=%s) parent entity %s to a miso entity. Cast to Asset entity." % 
                                (entity_data['code'], entity_data['entity']))
                entity_data['entity'] = {'entity_type':ENT_PROJ,'id':self._show_id}
                
            parent_entity_type = entity_data['entity']['entity_type'] 
            ent = entity_class ( entity_id      = entity_id,
                                 entity_code    = entity_data['code'],                              
                                 entity_data    = entity_data,
                                 version_num    = ver_num, 
                                 artist         = entity_data['created_by'],         
                                 publish_date   = entity_data['created_at'],   
                                 description    = entity_data['description'],
                                 status         = entity_data['sg_status_list'],
                                 
                                 for_review     = None,
                                 task           = {'entity_type':ENT_TASK, 
                                                    'id':entity_data['sg_task']['id']} \
                                                        if entity_data['sg_task'] else None,
                                 department     = None, #(ENT_DEPTentity_data['sg_task.Task.step'],
                                 
                                 parent_meta    = {'entity_type':parent_entity_type, 
                                                    'id': entity_data['entity']['id'] \
                                                        if entity_data['entity'] else None,
                                                    },
                                 )
            
        elif entity_type == ENT_VIDEO_CLIP:
            ent = self.objectfy_frame_submission_entity( entity_id, entity_data )
            
        else:
            raise ObjectfyEntityError, "Entity Type '%s' currently not supported." % entity_type

        return ent
    
    
    def objectfy_frame_submission_entity(self, entity_id, entity_data ):
        raise NotImplementedError 


    def list_sequences(self):
        '''
        @return list of scene objects in project
        @return list of search results. Each search result is a tuple ( entity_id, entity_data )
        '''
        result = self._find('Sequence',[ ('project','is',{'type':'Project','id':self._show_id} ) ],
                         DB_FIELDS[ENT_SEQ])
                                                                                
        return [ (r['id'], r) for r in result]
    
    
    def get_show(self):
        '''
        @return the show information, show id, code, and name.
        '''
        return {    'id': self._show_id,
                    'code': self._show_code,
                    'label': self._show_label }     
        
        
    def get_sequence(self, seq_code=None, seq_id=None):

        if seq_code!=None:
            seq_filter = ( 'code', 'is', seq_code )
        elif seq_id!=None:
            seq_filter = ('id', 'is', seq_id )
            
        result = self._find('Sequence',[ ('project','is',{'type':'Project','id':self._show_id} ),
                                             seq_filter ],
                         DB_FIELDS[ENT_SEQ])
        if result:                                                                        
            return  (result[0]['id'], result[0])   
        else:
            raise KeyError, "Can not find sequence with code '%s', id '%s'" % (seq_code, seq_id) 
            
    
    def list_shots(self, seq_obj):        
        '''        
        @param scene_obj
        @return list of shot objects that are in the scene         
        '''        
        #TODO: make a better query using assets to asset relation ship, rather than just using scene code.
        
        if seq_obj=='all':
            seq_filter = ('project', 'is', {'type':'Project','id':self._show_id} )
        else:
            seq_filter = ('sg_sequence', 'is', {'type': 'Sequence', 'id': seq_obj.entity_id() } )
                    
        result = self._find('Shot', [ seq_filter ], DB_FIELDS[ENT_SHOT] )
 
        return [ (r['id'], r) for r in result ]


    def list_assets(self, asset_type=None):
        '''
        @param asset_type 
        @return list of search results. Each search result is a tuple ( entity_id, entity_data )
        '''

        result = self._find('Asset',
                                    [ ('project','is', {'type':'Project','id':self._show_id} ),
                                       ('sg_asset_type','is', asset_type) ],
                                        DB_FIELDS[ENT_ASSET])
                                                                                
        return [ (r['id'], r) for r in result]

    
    def list_clips_from_versions(self, version_list ):
        '''
        @param version_id_list
        '''
        raise NotImplementedError
        
        
    def list_tasks(self, entity_type=None, entity_id=None, task_id=None, query_limit=500 ):
        '''     
        Retrieve the tasks for an entity, or tasks that match the task_id(s)   
        @param entity_type not need.
        @param entity_id the entity of the parent asset 
        @param task_id
        @return return list of task associated with the entity
        '''    
        filter = []
        if entity_type and entity_id!=None:
            filter.append( ('entity','is', {'type':ENT_2_SG_TYPE[entity_type], 'id':  entity_id } ) )
        
        else:
            if type(task_id) == int:
                task_id = [ task_id ]
                
            filter.append( ('id','in', task_id) )
            
        result = self._find('Task', filter, DB_FIELDS[ENT_TASK], limit=query_limit )
                 
        
        return [ (r['id'], r) for r in result ] 
    
    
    
    def list_versions(self, entity_meta_list   = None,
                        
                            task_type_code     = None, 
                            status             = False,
                            
                            version_type       = None,
                       
                            artist             = None,
                            start_time         = None,
                            end_time           = None,  
                        
                            ent_limit          = 111,
                            ver_limit          = 500):
        '''
        List the version for the entity with filters latest only (only return one record), tagged for review
        @param entity_meta_list list of entity meta dictionary ex:[ {'entity_type':ENT_SHOT, 'id':5 },...]
        @param latest_only
        @param task_code [optional] return version related to task type, can be a list
        @param query_entity_limit [optional, default=111] The limit on the entity query
        @param status [optional] return only marked with status.
        @type status string, list
        @param version_type [optional] 
        @type version_type string, list
        @return version entities relating to shot or asset entity
        @rtype [ Version ] 
        '''        
        filters = []
         
        filters.append( ('project','is', {'type':'Project','id':self._show_id} ))
            
        if entity_meta_list:
            ent_list = []
            for entity_dict in entity_meta_list:
                ent_list.append( { 'type': ENT_2_SG_TYPE[entity_dict['entity_type']], 
                                   'id': entity_dict['id'] } )
                
            filters.append( ('entity','in', ent_list) ) 
            
        if version_type!=None:
            if type(version_type) in (str, unicode):
                version_type = [version_type]            
            filters.append( ('sg_version_type','in', version_type))
            
        if task_type_code!=None:
            if type(task_type_code) in (str, unicode):
                task_type_code = [task_type_code]
            filters.append( ('sg_task.Task.content','in', task_type_code))
        
        result = self._find('Version',
                               filters,
                               DB_FIELDS[ENT_VERSION],
                               limit   = ver_limit,
                               order   = [{'field_name':'id','direction':'desc'}] )
              
        return [ (r['id'], r) for r in result ]  


    def list_versions_latest(self, entity_meta_list,
                              
                                task_type_code     = None, 
                                for_review_only    = False,
                          
                                artist             = None,
                                start_time         = None,
                                end_time           = None,   
                                
                                version_type       = None,
                                
                                ent_limit          = 500,
                                ver_limit          = 1000, 
                                include_retired    = False):
        '''
        List the version for the entity with filters latest only (only return one record), tagged for review
        @param entity_type not used since entity_id is enough to identify entity
        @param entity_id can be a list
        @param latest_only
        @param task_type_code [optional] return version related to task type, can be list.
        @param for_review_only [optional] return only marked for review versions.
        @param query_entity_limit [optional, default=111] The limit on the entity query
        @return version entities relating to shot or asset entity
        @rtype [ Version ] 
        '''        
        filters = []
         
        filters.append( ('project','is', {'type':'Project','id':self._show_id} ))
        
        query_entity_type = None
        if entity_meta_list:
            # build list of entities to filter
            ent_list = []
            for entity_dict in entity_meta_list:
                
                ent_list.append( { 'type':  ENT_2_SG_TYPE[entity_dict['entity_type']], 
                                   'id':    entity_dict['id'] } )
                
            filters.append( ('entity','in', ent_list) ) 
            
            # ensure only one entity type and entity type is one of shot or asset
            entity_types = [ d['entity_type'] for d in entity_meta_list ]
            assert len(set(entity_types)) == 1, \
                "Querying for latest requires one entity_type, given %s" % set(entity_types) 
            query_entity_type = entity_types[0]
            assert query_entity_type in (ENT_ASSET, ENT_SHOT), \
                "Currently only support querying latest for shot and assets. Given '%s'" % query_entity_type
        
        if type(task_type_code) in (str, unicode): 
            task_type_code = [task_type_code]
            
        if task_type_code!=None and len(task_type_code)!=0:
            filters.append( ('sg_task.Task.content','in', task_type_code))
        
        # summarize and group by task and entity and summary by biggest id
        summary = self._summarize('Version', filters, 
                             # make assumption that id only ever goes up. Hence, higher id, the later the publish date
                             summary_fields = [{'field':'id', 'type':'maximum'}],  
                             grouping       = [{'field':('entity.Shot.code' 
                                                            if query_entity_type==ENT_SHOT  
                                                            else 'entity.Asset.code'),
                                                'type':'exact','direction':'asc'},
                                               {'field':'sg_task.Task.content','type':'exact','direction':'asc'}] )
        
        # now collect all the version ids
        ver_id_list = []
        if summary.has_key('groups'):
            for ent_summary in summary['groups']: 
                if ent_summary.has_key('groups'):
                    for v in ent_summary['groups']:                        
                        ver_id_list.append( v['summaries']['id'] )
            
        
        # now query for the version associate with the biggest id
        result = []
        if ver_id_list:
            result = self._find('Version', [ ['id', 'in', ver_id_list] ], 
                                     DB_FIELDS[ENT_VERSION], limit   = ver_limit )       
        
              
        return [ (r['id'], r) for r in result ]  

    
    
    def get_shot_audio(self, shot_entity):
        '''
        Returns the path, and the offset
        @rtype: str
        '''
        audio_version = shot_entity.task('snd').latest_version()
        
        if audio_version:
            return audio_version.path()
        else:
            LOG.warning("No audio found for entity %s" % shot_entity.entity_code() )
            return None     
        
    
    
    def get_shot(self, shot_code=None, shot_id=None, seq_id=None):
        filters = [ ('project','is',{'type':'Project','id':self._show_id} ) ]
        
        if shot_code!=None:
            filters.append( ('code', 'is', shot_code ) )
            
        elif shot_id!=None:
            filters.append(  ('id', 'is', shot_id ) )
            
        if seq_id:
            filters.append(  ('sg_sequence', 'is', {'type':'Sequence','id':seq_id} ) )
            
        result = self._find('Shot', filters, DB_FIELDS[ENT_SHOT])
        
        if result:                                                                        
            return  (result[0]['id'], result[0]) 

        
    
    
    def get_asset(self, asset_code=None, asset_id=None, asset_type=None):
        '''
        Get the asset, either by asset code or by asset id
        This can be any asset, which can also include shots.
        
        @param asset_code can be list
        @param asset_id can be list
        @return the entity_code, and the entity data pair
        '''
        filter = [ ('project','is', {'type':'Project','id':self._show_id} ) ]
        if asset_code!=None:
            filter.append( ('code','is', asset_code))
            
        elif asset_id!=None:
            filter.append( ('id','is', asset_id) )
            
        if asset_type!=None:
            filter.append( ('sg_asset_type','is', asset_type))
        
        r = self._find('Asset', filter, DB_FIELDS[ENT_ASSET])
        
        criteria_str = "asset code='%s' id='%s' type='%s'" % (asset_code, asset_id, asset_type)
        if len(r) > 1:
            LOG.warning( "There are more than one asset given [%s]: %s" % ( criteria_str,
                                                                            pformat(r)))  
        elif len(r) ==0:
            raise KeyError, "Can not find asset matching criteria [%s]" % criteria_str  
                                                                     
        return r[0]['id'], r[0]

        
    
    def batch_list_entities(self, entity_code=None, entity_id=None, search_query=None):
        '''
        batch get the entities
        @param entity_code can be list
        @param entity_id can be list
        @param search_query query regular expression ex: 'sc0120', 'bike', '^bike[0-9]'        
        '''
        raise NotImplementedError


    def get_task(self, task_id ):
        '''
        @param task_id 
        @return return the task
        '''
        result = self._find('Task', [ [ 'id', 'is', task_id ] ], DB_FIELDS[ENT_TASK]  )                      
                 
        if result:                                                                        
            return  (result[0]['id'], result[0]) 


    
    def get_source_path( self, version ):
        '''
        Given the version entity, return the source path of the file associated with version.
        @param version is the version entity
        '''
        raise NotImplementedError
    
    
    def clear_cached(self):
        '''
        Purge the cached data.
        '''
        self.__cached_tasks_types  = None   # stores the raw assets type query from       
    
    
    def get_status(self, status):
        '''
        @return the status meta data from the status id or status code
        '''
        return self._cached_status_types(status)
    
    
    def get_user(self, user):
        '''
        @return the user meta data from the id or form the code
        '''
        return self._cached_users(user)        
            
    
    def get_task_type(self, task_ent):
        raise NotImplementedError

    
    
    def _cached_tasks_types(self, task_type_id ):
        '''
        Return list of task types
        @return hash sorted by slug ex: {ENT_SCENE: {'slug':'sh','id':'93', 'name':'Shot'} }
        '''      
        if self.__cached_tasks_types==None:
            result = self._find('Task',[('task_template','is_not',None)], DB_FIELDS[ENT_TASK_TYPE])
            unique_name_list = [] 
            self.__cached_tasks_types = {}
            for r in result:
                if r['content'] not in unique_name_list:
                    unique_name_list.append(r['content'])
                    self.__cached_tasks_types[r['content']] =  r
        
        if task_type_id=='all':            
            return self.__cached_tasks_types
        
        elif task_type_id in self.__cached_tasks_types:
            return self.__cached_tasks_types[task_type_id]
        else:
            LOG.warning("Can not find task type of id %s." % task_type_id)
            return None
            
        
    def _cached_users(self, user_id ):
        '''
        @return list of user meta
        '''
        raise NotImplementedError 

    
    def list_submission_types(self):
        '''
        @return list of submission types
        '''
        raise NotImplementedError 
    
    
    def list_status_types(self):
        '''
        @return a list of all the status
        @rtype [ (id, meta) ] 
        '''
        raise NotImplementedError 
    
 
    def list_task_types(self, entity_type):
        '''
        @return a list of all task types
        @rtype [ (id, meta) ]
        '''
        all_task_types = self._cached_tasks_types('all')
         
        return [ (k, all_task_types[k]) for k in all_task_types 
                    if all_task_types[k]['task_template.TaskTemplate.entity_type'] == ENT_2_SG_TYPE[entity_type] ]
     
    

    def set_task_status(self, task_id, status_id, user_id, tech=False):
        '''
        Set the task to the status.
        @param task_id
        @param status_id
        @param tech status or normal        
        '''        
        raise NotImplementedError
        
        
        
    def create_version(self, task_entity, source_path, comment, artist, date ):
        '''
        @param task_entity
        @type task_entity: miso.entity_factory.Task 
        @param source_path
        @param artist - user code, ie pparker
        '''   
        raise NotImplementedError
        
        

    def create_frame_submission(self, 
                                version_entity, source_path, preview_path,
                                start_frame, end_frame,
                                tags,
                                submit_type, file_type,   
                                ):
        '''
        @param task_entity
        @type task_entity: miso.entity_factory.Task 
        @param source_path
        @param artist - user code, ie pparker
        '''

        raise NotImplementedError
            
                
        
        
    