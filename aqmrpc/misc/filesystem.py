'''
Created on Mar 12, 2012

@author: arif
'''

import os.path


def path_inside(base, path):
    '''
    Check whether path is inside base directory.
    return True or False
    '''
    base = os.path.abspath(base)
    path = os.path.abspath(path)
    if len(path) < len(base):
        return False
    if path[:len(base)] == base:
        return True
    else:
        return False
    