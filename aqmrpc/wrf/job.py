'''
'''
from twisted.python import log

from aqmrpc.wrf import environment as wrfenv
from servercon import supervisor

from aqmrpc.models import CurrentJob
from aqmrpc.jobs import manager as jobmanager

from aqmrpc.misc.rest_client import command_confirm_run, command_report_run_stage, command_job_finished

class WRFRun(supervisor.BaseJob):
    def __init__(self, data, callback=None, envid=None):
        '''
        WRF modeling job.
        data['name']: name identifying this job
        data['task_id']: task id from web interface
        data['WRFnamelist']: WRF namelist string data
        data['WPSnamelist']: WPS namelist string data
        data['ARWpostnamelist']: ARWpost namelist string data
        data['grads_template']: grads script template
        '''
        super(WRFRun, self).__init__(runner=supervisor.RUNNER_CPUBOUND,
                                     callback=callback)
        self.name = '<WRF> %s' % data['name']
        self.data = data
        self.envid = envid
        self.env = None
        self.jobentry = None
        
    def set_up(self):
        # TODO: ask the web interface if the job is not canceled
        try:
            ret = command_confirm_run(self.data['task_id'])
        except Exception, e:
            log.err(e, '[Job] Exception in command_confirm_run')
            return False
        
        if ret != True:
            return False
        
        # open wrf environment
        self.env = wrfenv.Env(self.envid)
        
        # creates the environment
        self.env.setup()
        
        if self.envid is None:
            self.envid = self.env.envid
        
        # TODO: setup log rotation
        
        # setup namelist file
        self.env.set_namelist('WRF', self.data['WRFnamelist'])
        self.env.set_namelist('WPS', self.data['WPSnamelist'])
        
        # increment job count
        jobmanager.increment_job()
        
        # TODO: create database entry for current wrf job
        self.jobentry = CurrentJob(name=self.name, envid=self.envid,
                                   job_type=self.__class__.__name__)
        self.jobentry.save()
        
        stage = 'Model Preparation'
        try:
            command_report_run_stage(self.data['task_id'], self.envid, stage)
        except Exception, e:
            log.err(e, '[Job] Exception in command_report_run_stage')
            
        return True
        
    
    def tear_down(self):
        # cleanup wrf environment
        
        # decrement job count
        jobmanager.decrement_job()
        
        # remove database entry for current wrf job
        self.jobentry.delete()
    
    def callback(self):
        # TODO: tell the web interface the job is finished
        try:
            ret = command_job_finished(self.data['task_id'])
        except Exception, e:
            log.err(e, '[Job] Exception in command_job_finished')
        
    
    def process(self):
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'prepare_wps'
        self.jobentry.save()
        self.env.prepare_wps()
        
        
        stage = 'WPS'
        try:
            command_report_run_stage(self.data['task_id'], self.envid, stage)
        except Exception, e:
            log.err(e, '[Job] Exception in command_report_run_stage')
        
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'run_wps'
        self.jobentry.save()
        self.env.run_wps()
        
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'cleanup_wps'
        self.jobentry.save()
        self.env.cleanup_wps()
        
        
        stage = 'WRF'
        try:
            command_report_run_stage(self.data['task_id'], self.envid, stage)
        except Exception, e:
            log.err(e, '[Job] Exception in command_report_run_stage')
            
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'prepare_wrf'
        self.jobentry.save()
        self.env.prepare_wrf()
        
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'run_wrf'
        self.jobentry.save()
        self.env.run_wrf()
        
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'cleanup_wrf'
        self.jobentry.save()
        self.env.cleanup_wrf()
        
        stage = 'ARWpost'
        try:
            command_report_run_stage(self.data['task_id'], self.envid, stage)
        except Exception, e:
            log.err(e, '[Job] Exception in command_report_run_stage')
            
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
        self.jobentry.step = 'run_arwpost'
        self.jobentry.save()
        self.env.run_arwpost(self.data['ARWpostnamelist'])
        
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            # job does not exist, probably canceled
            return
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
        self.jobentry = None
    
    def set_up(self):
        # open wrf environment
        self.env = wrfenv.Env(self.envid)
        
        # creates the environment
        self.env.setup()
        
        # TODO: setup log rotation
        
        # setup namelist file
        #self.env.set_namelist('WRF', self.data['WRFnamelist'])
        #self.env.set_namelist('WPS', self.data['WPSnamelist'])
        
        # Try to get the job record from database
        try:
            self.jobentry = CurrentJob.objects.get(envid=self.envid)
        except CurrentJob.DoesNotExist:
            self.jobentry = None
    
    def tear_down(self):
        # remove job entry from database
        if self.jobentry is not None:
            # decrement job count
            jobmanager.decrement_job()
            
            self.jobentry.delete()
            
    
    def process(self):
        # try to reconnect to running process
        pass
    