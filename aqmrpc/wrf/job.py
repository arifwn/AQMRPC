'''
'''

from aqmrpc.wrf import environment as wrfenv
from servercon import supervisor

class WRFRun(supervisor.BaseJob):
    def __init__(self, name, callback=None, envid=None):
        super(WRFRun, self).__init__(name=('<WRF> %s' % name),
                                     runner=supervisor.THREAD_POOL_CPUBOUND_SIZE,
                                     callback=callback)
        self.envid = envid
        self.e = None

    def set_up(self):
        # open wrf environment
        self.e = wrfenv.Env(self.envid)
    
    def tear_down(self):
        # cleanup wrf environment
        pass
    
    def process(self):
        # prepare wrf environment
        
        # prepare data and configuration
        
        # run models
        
        # process results
        
        # cleanup
        
    