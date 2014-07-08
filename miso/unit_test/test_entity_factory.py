from pprint import pprint, pformat

import unittest, os, sys, logging
import miso
import miso.config

LOG = miso.config.get_logger()

class TestProdb(unittest.TestCase):
    '''
    Extends the unittest.TestCase for testing media module  
    '''
    def setUp(self):
        '''
        setup the test, this is call before each test 
        '''
        self.proj = miso.get_project('bbb')  # project code 'bbb' for 'big buck bunny'
        logging.getLogger().setLevel(10)

        
    def tearDown(self):
        '''
        test finish, clean up any dummy files
        '''
        print "DB Access Summary: ", pformat(self.proj.db_access_metric())
        

    def test_list_sequences(self):
        seq = self.proj.list_sequences()[0]
        
        assert seq.entity_type() == miso.ENT_SEQ


    def test_get_sequence(self):        
        
        seq = self.proj.sequence('bunny_010')
        
        assert seq.entity_type() == miso.ENT_SEQ
        
        seq_obj_by_id = self.proj.sequence( seq_id = seq.entity_id() ) 
                   
        
        # ensure the scene return by code or by id is the same. 
        assert seq==seq_obj_by_id

    
    def test_list_shots(self):
        
        # query list all shots
        result = self.proj.list_shots()
         
        assert result[0].entity_type() == miso.ENT_SHOT, "Failed to query all shots"
        
        # query list shot from a scene
        shot = self.proj.list_shots('bunny_010')[0]
        
        assert shot.sequence().entity_code() == 'bunny_010', "Failed to query shot from scene"
        
        # list shots from scene
        seq = self.proj.sequence('bunny_010')
        shot = seq.list_shots()[0]
        
        assert shot.entity_type() == miso.ENT_SHOT
        
    
    
    def test_get_shot(self):
    
        # query shot directly
        shot = self.proj.shot('bunny_010_0010')
        
        assert shot.entity_code() == 'bunny_010_0010', "Failed to query shot directly"
        
        # query the shot from the sequence
        
        shot_via_seq = self.proj.sequence('bunny_010').shot('bunny_010_0010')
        
        assert shot==shot_via_seq, "Error: Shot query from project not the same as shot."
        
        
        
    def test_get_shot_cut(self):
        shot = self.proj.shot('bunny_010_0010')
        assert type( shot.edit_cut() ) in (tuple, list)
        


    def test_list_assets(self):
        char = self.proj.list_assets('Character')[0]

        assert char.entity_type() == 'Asset'
        assert char.asset_type() == 'Character'                                                                                                                                                                                                                                                       
        
        result = self.proj.list_assets([ 'Character', 'Prop'] )
        
        assert result[0].asset_type() == 'Character'
        assert result[-1].asset_type() == 'Prop'
        
        
    
    def test_list_task(self):
        
        shot_obj = self.proj.shot('bunny_010_0010')
        
        # get the task from the project
        task_list = self.proj.list_tasks( miso.ENT_SHOT, shot_obj.entity_id() )        
        
        # can also directly get the task from shot object
        assert shot_obj.list_tasks()[0].entity_id() == task_list[0].entity_id()
   
        light_task = shot_obj.task('Light')
        assert light_task!=None
        
        asset_obj = self.proj.asset('alice')
        asset_obj.list_tasks()
     
        
        
    def test_get_asset(self):
        asset_obj = self.proj.asset('Alice', asset_type = 'Character')
        asset_obj = self.proj.asset('Fern')
        
        LOG.debug( '> asset: %s' % str(asset_obj) )
        LOG.debug( asset_obj.entity_type() )
        LOG.debug( asset_obj.entity_code() )        
        LOG.debug( asset_obj.entity_label() )
        
        # can also get by id
        asset_obj = self.proj.asset(asset_id=asset_obj.entity_id() )
        
        assert asset_obj==asset_obj
        
        
    def test_get_asset_task(self):
        raise NotImplementedError  
    
    
    def test_list_task_types(self):
        tt_shot = self.proj.list_task_types(miso.ENT_SHOT)
        
        LOG.info( "Shot task types: ")
        for t in tt_shot:
            LOG.info(t)
        
        tt_asset = self.proj.list_task_types( miso.ENT_ASSET )
        
        LOG.info( "Asset task types: %s" % [ t.entity_code() for t in tt_asset ] ) 
               
        
        
    def test_list_versions(self):

        shot_ver = self.proj.shot('bunny_010_0010').task('Anm').list_versions().filter(version=3)[0]
    
        assert shot_ver.task().entity_code() == 'Anm'
        assert shot_ver.version() == 3
        assert shot_ver.parent().entity_code() == 'bunny_010_0010' 
          
        asset_ver = self.proj.asset('Buck').task('Rig').list_versions().filter(version=1)[0]
    
        assert asset_ver.task().entity_code() == 'Rig'
        assert asset_ver.version() == 1
        assert asset_ver.parent().entity_code() == 'Buck'    


    def test_list_latest_versions(self):
        latest_result = self.proj.shot('bunny_150_0200').list_versions(latest_only=True)
        
        # since it's latest summarize by task type, the number of task type should equal to result
        assert len(latest_result) == len(latest_result.list_tasks()), "Unexpected number of results."
        
        # different way to get the latest
        anm_latest_ver = self.proj.shot('bunny_150_0200').task('Anm').latest_version()
        
        assert anm_latest_ver.version() == latest_result.filter(task_code='Anm')[0].version()
        

    def test_batch_list_versions(self):
        '''
        list version for multiple objects
        '''
        s = self.proj.shot('bunny_150_0200')
        
        # list version for a list of entities using by resgular, and latest query
        all_result     = self.proj.list_versions( [s])
        latest_result  = self.proj.list_versions( [s], latest_only=True)
        
        # ensure the result has same type of task
        assert len(all_result) >= len(latest_result)
        assert all_result.list_tasks() == latest_result.list_tasks()
        
        for task_code in latest_result.list_tasks():
            assert len(latest_result.filter(task_code=task_code)) == 1
        
        assert all_result.filter(task_code='Light')[0] == latest_result.filter(task_code='Light')[0]
        
        
        
      
        



READ_TEST_SUITE = unittest.TestSuite()
WRITE_TEST_SUITE = unittest.TestSuite()
BATCH_READ_TEST_SUITE = unittest.TestSuite()

####### read test ########
READ_TEST_SUITE.addTest( TestProdb('test_list_sequences') )
     
READ_TEST_SUITE.addTest( TestProdb('test_get_sequence') )
READ_TEST_SUITE.addTest( TestProdb('test_list_shots') )
READ_TEST_SUITE.addTest( TestProdb('test_get_shot') )
READ_TEST_SUITE.addTest( TestProdb('test_get_shot_cut') )
READ_TEST_SUITE.addTest( TestProdb('test_list_task') )
       
READ_TEST_SUITE.addTest( TestProdb('test_get_asset') )
READ_TEST_SUITE.addTest( TestProdb('test_list_assets') )
   
READ_TEST_SUITE.addTest( TestProdb('test_list_task_types') )   
READ_TEST_SUITE.addTest( TestProdb('test_list_versions') )
READ_TEST_SUITE.addTest( TestProdb('test_list_latest_versions') )

  
# READ_TEST_SUITE.addTest( TestProdb('test_list_clips_from_version') )
#  
#   
# ####### batch read test ########
# BATCH_READ_TEST_SUITE.addTest( TestProdb('test_batch_list_entities') )
# BATCH_READ_TEST_SUITE.addTest( TestProdb('test_batch_list_versions') )
# BATCH_READ_TEST_SUITE.addTest( TestProdb('test_batch_list_latest_for_scene') )
# 
# ####### write test ########
# WRITE_TEST_SUITE.addTest( TestProdb('test_create_version') )
# WRITE_TEST_SUITE.addTest( TestProdb('test_create_frame_submission') )



if __name__ == "__main__":
    error_num = 0
    fail_num = 0
     
    for test_suite in [ 
                       unittest.TextTestRunner(verbosity=2).run( BATCH_READ_TEST_SUITE ), 
                       unittest.TextTestRunner(verbosity=2).run( READ_TEST_SUITE ),
                       unittest.TextTestRunner(verbosity=2).run( WRITE_TEST_SUITE )
                       ]:
        error_num += len ( test_suite.errors )
        fail_num += len ( test_suite.failures ) 
    
    print "Number of Errors: %s" % error_num
    print "Number of Fails: %s" % fail_num
    
    
    
    
    
    
    
    
    
    
    
    
    
        
