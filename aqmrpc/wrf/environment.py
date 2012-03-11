'''
Created on Feb 24, 2012

@author: arif
'''

import os
from os import path
import shutil

from aqmrpc import settings


def verify_id(envid):
    '''check if given environment id is actually valid and exist'''
    if ('.' in envid) or ('/' in envid):
        # suspicious id
        return False
    envpath = working_path(envid) 
    try:
        os.stat(envpath)
        return True
    except OSError:
        return False

def working_path(envid):
    '''return base path of the modeling environment identified with id''' 
    return path.join(settings.AQM_WORKING_DIR, envid)

def program_path(envid, program):
    return path.join(settings.AQM_WORKING_DIR, envid, program)

def setup(envid):
    '''create a new modeling environment in AQM_WORKING_DIR location
    return model working path'''
    base = working_path(envid)
    
    # recursively create symlinks to all items in AQM_MODEL_DIR
    master_path = path.join(settings.AQM_MODEL_DIR, 'WRF')
    if not path.exists(master_path):
        raise Exception('invalid AQM_MODEL_DIR setting')
    
    try:
        os.stat(base)
        # environment with specified id is already exist
        return False
    except OSError:
        pass
    
    master_tree = os.walk(master_path)
    os.mkdir(base)
    for cwd, dirs, files in master_tree:
        working_cwd = path.join(base, cwd[len(master_path)+1:])
        for dr in dirs:
            os.mkdir(path.join(working_cwd, dr))
        for f in files:
            os.symlink(path.join(cwd, f), path.join(working_cwd, f))
    
    return True

def cleanup(envid):
    '''remove a modeling environment identified with id'''
    try:
        shutil.rmtree(working_path(envid))
    except OSError:
        pass
    
