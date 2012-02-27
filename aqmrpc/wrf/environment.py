'''
Created on Feb 24, 2012

@author: arif
'''

import os
from os import path
import shutil

from aqmrpc import settings


def working_path(id):
    '''return base path of the modeling environment identified with id''' 
    return path.join(settings.AQM_WORKING_DIR, id)

def setup(id):
    '''create a new modeling environment in AQM_WORKING_DIR location
    return model working path'''
    base = working_path(id)
    
    # TODO: recursively create symlinks to all items in AQM_MODEL_DIR
    master_path = path.join(settings.AQM_MODEL_DIR, 'WRF')
    if not path.exists(master_path):
        raise Exception('invalid AQM_MODEL_DIR setting')
    
    master_tree = os.walk(master_path)
    os.mkdir(base)
    for cwd, dirs, files in master_tree:
        working_cwd = path.join(base, cwd[len(master_path)+1:])
        for dr in dirs:
            os.mkdir(path.join(working_cwd, dr))
        for f in files:
            os.symlink(path.join(cwd, f), path.join(working_cwd, f))
    
    return base

def cleanup(id):
    '''remove a modeling environment identified with id'''
    shutil.rmtree(working_path(id))
    
