'''
Created on Jan 28, 2012

@author: arif
'''

from twisted.python import log

from servercon.supervisor import Job


class TestJob(Job):
    
    def __init__(self, name=None, data=None):
        super(TestJob, self).__init__(name=name)
        if self.name is None:
            self.name = 'Test Job'
        self.data = data
    
    def process(self):
        if self.data is None:
            log.msg('test job invoked!')
        else:
            log.msg(self.data)
    