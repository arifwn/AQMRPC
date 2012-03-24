'''
'''

from aqmrpc.wrf import environment as wrfenv
from servercon import supervisor

from aqmrpc.models import CurrentJob

class WRFRun(supervisor.BaseJob):
    def __init__(self, name, data, callback=None, envid=None):
        '''
        WRF modeling job.
        name: name identifying this job
        data['WRFnamelist']: WRF namelist string data
        data['WPSnamelist']: WPS namelist string data
        data['ARWpostnamelist']: ARWpost namelist string data
        data['grads_template']: grads script template
        '''
        super(WRFRun, self).__init__(name=('<WRF> %s' % name),
                                     runner=supervisor.THREAD_POOL_CPUBOUND_SIZE,
                                     callback=callback)
        self.data = data
        self.envid = envid
        self.env = None
        self.jobentry = None
        
        # TODO: make the job persistent to disk in case of rpc server error

    def set_up(self):
        # open wrf environment
        self.env = wrfenv.Env(self.envid)
        
        # creates the environment
        self.env.setup()
        
        # TODO: setup log rotation
        
        # setup namelist file
        self.env.set_namelist('WRF', self.data['WRFnamelist'])
        self.env.set_namelist('WPS', self.data['WPSnamelist'])
        
        # TODO: create database entry for current wrf job
        self.jobentry = CurrentJob(name=self.name, envid=self.envid,
                                   job_type=self.__class__.__name__)
        self.jobentry.save()
        
    
    def tear_down(self):
        # cleanup wrf environment
        pass
    
        # TODO: remove database entry for current wrf job
        self.jobentry.delete()
    
    def process(self):
        
        self.jobentry.step = 'prepare_wps'
        self.jobentry.save()
        self.env.prepare_wps()
        
        self.jobentry.step = 'run_wps'
        self.jobentry.save()
        self.env.run_wps()
        
        self.jobentry.step = 'cleanup_wps'
        self.jobentry.save()
        self.env.cleanup_wps()
        
        self.jobentry.step = 'prepare_wrf'
        self.jobentry.save()
        self.env.prepare_wrf()
        
        self.jobentry.step = 'run_wrf'
        self.jobentry.save()
        self.env.run_wrf()
        
        self.jobentry.step = 'cleanup_wrf'
        self.jobentry.save()
        self.env.cleanup_wrf()
        
        self.jobentry.step = 'run_arwpost'
        self.jobentry.save()
        self.env.run_arwpost(self.data['ARWpostnamelist'])
        
        self.jobentry.step = 'run_grads'
        self.jobentry.save()
        self.env.render_grads(self.data['grads_template'])


class WRFResume(supervisor.BaseJob):
    pass
    
    # get last running state of the model
    # if last running state is WPS, try to resume WPS programs
    # and continue with WRF and ARWpost
    # and so on...
    # 
    
    def __init__(self, name, data, callback=None, envid=None):
        '''
        WRF modeling job.
        name: name identifying this job
        data['WRFnamelist']: WRF namelist string data
        data['WPSnamelist']: WPS namelist string data
        data['ARWpostnamelist']: ARWpost namelist string data
        data['grads_template']: grads script template
        '''
        super(WRFRun, self).__init__(name=('<WRF> %s' % name),
                                     runner=supervisor.THREAD_POOL_CPUBOUND_SIZE,
                                     callback=callback)
        self.data = data
        self.envid = envid
        self.env = None
    