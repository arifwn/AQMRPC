'''
Created on Feb 24, 2012

@author: arif
'''

class BaseController(object):
    
    @property
    def status(self):
        '''return running status of the model environment'''
        raise NotImplementedError()
    
    @property
    def ready(self):
        '''True if model environment is set up properly'''
        raise NotImplementedError()
