import os

def get_root_path( *token ):    
    return get(*token)


def get( *token ):
    
    if token:
        return os.path.join( os.path.split(__file__)[0], *token )
    else:
        return os.path.split(__file__)[0]
    
    
