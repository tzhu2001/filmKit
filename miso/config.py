import os, logging

url, user, key = [ t.strip() for t in open(r'C:\tmp\shotgun_conn\shotgun_conn.txt').read().split('\n')[0].split(',') ]

prod_db_conn_param = {
                      ('bbb','prod'):{
                                        'type': 'shotgun',
                                        'name': 'Big Buck Bunny',
                                        'url':  url,
                                        'user': user,
                                        'key':  key,
                                        }, 
                      ('dap','prod'):{
                                        'type': 'shotgun',
                                        'url':  url,
                                        'user': user,
                                        'key':  key,
                                        },                       
                      ('spk','prod'):{
                                        'type': 'shotgun',
                                        'url':  url,
                                        'user': user,
                                        'key':  key,
                                        },                        
                      }

LOGGER = None

def get_logger():
    global LOGGER
    
    if LOGGER==None:
        LOGGER = logging
        
    return LOGGER
