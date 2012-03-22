'''
'''

from servercon import supervisor

class WRFRun(supervisor.BaseJob):
    def __init__(self, name, callback=None):
        super(WRFRun, self).__init__(name=name,
                                     runner=supervisor.THREAD_POOL_CPUBOUND_SIZE,
                                     callback=callback)

    