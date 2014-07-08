'''
This module keep tracks of all the company/show modification to shotgun schema.  
'''
CUSTOM_FIELDS = { 'Version':
                        [ # custom field for version starts         
                               {
                               'name':          'sg_version_number',
                               'label':         'Version Number', 
                               'type':          'number',
                               'description':   'Version number as an integer.'                     
                               },
#                                {
#                                'name':          'sg_login',
#                                'label':         'Login', 
#                                'type':          'text',
#                                'description':   'The user responsible for publishing the data.'
#                                },
                               {                                                                                
                               'name':          'sg_path',
                               'label':         'Path',
                               'type':          'text',
                               'description':   'This is path for general files like audio.',
                               },
#                                {
#                                'name':          'sg_parent_version',
#                                'label':         'Parent Version', 
#                                'type':          'entity',
#                                'valid_types':   ['Version', 'Step'],
#                                'description':   'Parent Version ex: source scene for render publish'                     
#                                },                 
                         ],
                 'Project':
                        [ # custom field for version starts         
                               {
                               'name':          'sg_code',
                               'label':         'Project code', 
                               'type':          'text',
                               'description':   'Project code.'                     
                               },
                         ]      
                }



CUSTOM_PROPERTIES = { 'Version':
                        [ # custom properties for version starts                                   
                              {
                               'name':  'sg_version_type',
                               'valid_values': ['video_clip', 'audio_clip', 'anim_scene'],
                               },          
                         ]
                     }

def update_schema(sg_conn, test=True):
    '''
    Update the entity schema for shotgun.
    '''
    for entity_type in CUSTOM_FIELDS:
        print '\n', '#' * 100 
        print 'Checking for new field for entity: "%s"...' % entity_type
        print '#' * 100
    
        current_schema = sg_conn.schema_field_read(entity_type) 
        
        for field_meta in CUSTOM_FIELDS[entity_type]:
            
            # shotgun automatically prefix all custom field with prefix 'sg_'            
            prefixed_name = field_meta['name'] if field_meta['name'].startswith('sg_') else 'sg_%s' % field_meta['name']
            create_name   = prefixed_name[3:] # the create name need to be without the 'sg_'
             
            if prefixed_name not in current_schema:
                print 'Creating entity "%s" custom field "%s" %s...\n' % ( entity_type, 
                                                                        create_name, 
                                                                        '[Test Only]' if test else '' ),
                
                if not test:
                    properties = field_meta
                    properties['name'] = create_name # so that it doesn't prefix sg_ twice
                    properties['summary_default'] = 'count'
                    label = properties['label']
                    field_type = properties['type']
                    del(properties['label'])
                    del(properties['type'])
                    
                    sg_conn.schema_field_create(entity_type, 
                                                field_type, 
                                                display_name    = label, 
                                                properties      = properties )
                    
                    print 'Done'
                    

def update_schema_properties(sg_conn, test=True):
    '''
    Update the entity properties schema for shotgun.
    '''    
    for entity_type in CUSTOM_PROPERTIES:
        print '\n', '#' * 100
        print 'Checking for custom properties updates for entity: "%s"...' % entity_type
        print '#' * 100
        
        current_schema = sg_conn.schema_field_read(entity_type)
                 
        for field_meta in CUSTOM_PROPERTIES[entity_type]:
            if field_meta['name'] not in current_schema:
                print 'Warning! The entity "%s" does not have field called "%s"' % (entity_type, field_meta['name'])
                continue

            # update properties 'valid values'
            if 'valid_values' in field_meta:  
                              
                current = current_schema[field_meta['name']]['properties']['valid_values']['value']
                
                _new = set(field_meta['valid_values']).difference(set(current))
                
                if _new:
                    print 'Adding new valid values to %s.%s: %s %s...' % (entity_type, field_meta['name'], list(_new),
                                                                        '[Test Only]' if test else ''),
                    if not test:
                        current.extend(list(_new))
                        sg_conn.schema_field_update(entity_type, 
                                                    field_meta['name'], 
                                                    {'valid_values':current}
                                                    )
                        print 'Done'      


if __name__ == "__main__":
    from shotgun_api3 import Shotgun
    
    url, user, key = [ t.strip() for t in open(r'C:\tmp\shotgun_conn\shotgun_conn.txt').read().split('\n')[0].split(',') ]  
        
    sg_conn    = Shotgun(url, user, key)
    
    update_schema(sg_conn, test=False)
    update_schema_properties(sg_conn, test=True)
    