'''
Created on Jan 28, 2012

@author: arif
'''

from twisted.python import log

from servercon.supervisor import Job


class TestJob(Job):
    
    def __init__(self, data=None):
        Job.__init__(self, 'Test Job')
        self.data = data
    
    def process(self):
        if self.data is None:
            log.msg('test job invoked!')
        else:
            log.msg(self.data)
    