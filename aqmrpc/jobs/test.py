'''
Created on Jan 28, 2012

@author: arif
'''

import time

from twisted.python import log

from servercon.supervisor import BaseJob, MODEL_POOL


class TestJob(BaseJob):
    
    def __init__(self, name=None, runner=None, data=None):
        super(TestJob, self).__init__(name=name, runner=runner)
        if self.name is None:
            self.name = 'Test Job'
        if self.runner is None:
            self.runner = MODEL_POOL
        self.data = data
    
    def process(self):
        log.msg('invoking test job in 10 s...')
        time.sleep(10)
        if self.data is None:
            log.msg('test job invoked!')
        else:
            log.msg(self.data)
    