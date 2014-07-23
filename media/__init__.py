from image_seq_util import * 

import subprocess
from pprint import pprint
import media.config

def run_and_log_cmd(cmd, block=True, root=None, shell=True, env=None):
    
    if media.config.DEBUG_LOG: 
        print "running command %s... \nunder root '%s'" % (cmd, root)
    
    if root:        # changed the running directory root
        cwd = os.curdir
        os.chdir(root)
    
    if block:
        print 'cmd: ', cmd
        if env:
            print "Overriding environment: ", 
            pprint (env)
            stdout, stderr = subprocess.Popen(cmd, shell=shell,
                                          stdin=subprocess.PIPE,  
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,                                          
                                          env=env
                                          ).communicate()
        else:
            stdout, stderr = subprocess.Popen(cmd, shell=shell, 
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,                                                       
                                          ).communicate()        
        
        print "problem running: result: \nout:'%s' \nerror:'%s'" % (stdout.strip(), stderr.strip())  
        
        if root: os.chdir(cwd)
        return stdout, stderr
        
    else:        
        print 'Subprocess called with: ', cmd, type(cmd), len(cmd)
        proc = subprocess.Popen(cmd, shell=shell)
        if root: os.chdir(cwd)
        
        return proc 