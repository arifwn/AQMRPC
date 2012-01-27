'''
Created on Jan 28, 2012

@author: arif
'''

from twisted.python import log

from servercon.supervisor import Job


class TestJob(Job):
    
    def __init__(self, *args, **kwargs):
        super(TestJob, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = 'Test Job'
        self.data = getattr(kwargs, 'data', None)
    
    def process(self):
        if self.data is None:
            log.msg('test job invoked!')
        else:
            log.msg(self.data)
    