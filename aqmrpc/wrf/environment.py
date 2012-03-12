'''
Created on Feb 24, 2012

@author: arif
'''

import os
from os import path
import shutil

from aqmrpc import settings


def verify_id(envid):
    '''Check if given environment id is actually valid and exist.'''
    envpath = working_path(envid) 
    try:
        os.stat(envpath)
        return True
    except OSError:
        return False

def working_path(envid):
    '''Return base path of the modeling environment identified with id.''' 
    return path.join(settings.AQM_WORKING_DIR, str(envid))

def program_path(envid, program):
    return path.join(settings.AQM_WORKING_DIR, str(envid), program)

def compute_path(envid, targetpath):
    '''Compute the real absolute path from environmental id and target path.'''
    return path.join(working_path(str(envid)), targetpath)

def get_geog_path():
    '''Return path to geog data.'''
    return path.join(settings.AQM_MODEL_DIR, 'WRF_DATA/geog')
    
def setup(envid):
    '''
    Create a new modeling environment in AQM_WORKING_DIR location.
    Return model working path.
    '''
    base = working_path(str(envid))
    
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
    '''Remove a modeling environment identified with id.'''
    try:
        shutil.rmtree(working_path(str(envid)))
    except OSError:
        pass
    
