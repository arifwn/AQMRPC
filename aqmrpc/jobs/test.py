'''
Created on Jan 28, 2012

@author: arif
'''

import time

from twisted.python import log

from servercon.supervisor import BaseJob, RUNNER_CPUBOUND


class TestJob(BaseJob):
    
    def __init__(self, name='Test Job', runner=RUNNER_CPUBOUND, data=None, callback=None):
        super(TestJob, self).__init__(name=name, runner=runner, callback=callback)
        self.data = data
    
    def process(self):
        log.msg('invoking test job in 5 s...')
        time.sleep(5)
        if self.data is None:
            log.msg('test job invoked!')
        else:
            log.msg(self.data)
    