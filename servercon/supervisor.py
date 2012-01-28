'''
Created on Jan 26, 2012

@author: arif
'''
import threading

from twisted.application import service
from twisted.python import log, threadpool
from django.conf import settings

import Queue

SUPERVISOR_POOL = 1
MODEL_POOL = 2
DOWNLOADER_POOL = 4

DEFAULT_POOL_SIZE = getattr(settings, 'DEFAULT_THREAD_POOL_SIZE', 20)
MODEL_POOL_SIZE = getattr(settings, 'MODEL_THREAD_POOL_SIZE', 10)
DOWNLOADER_POOL_SIZE = getattr(settings, 'DOWNLOADER_THREAD_POOL_SIZE', 10)

_supervisor = None

# default thread pool
_pool = None
_pool_lock = threading.RLock()

# modelling thread pool
_model_pool = None
_model_pool_lock = threading.RLock()

# downloader thread pool
_downloader_pool = None
_downloader_pool_lock = threading.RLock()
_jobs = Queue.Queue()


class BaseJob(object):
    
    def __init__(self, name=None, runner=None):
        self.name = name
        self.runner = None
    
    def set_up(self):
        pass
    
    def process(self):
        raise NotImplementedError()
    
    def tear_down(self):
        pass


class StopSupervisorJob(BaseJob):
    
    def __init__(self, name=None, runner=None):
        super(StopSupervisorJob, self).__init__(name=name, runner=runner)
        if self.name is None:
            self.name = 'Stop Supervisor'
    
    def process(self):
        global _supervisor
        _supervisor._exit_thread()


class SupervisorThread(threading.Thread):
    
#    daemon = True
    running = False
    
    def start(self):
        if self.running:
            return False
        else:
            self.running = True
            super(SupervisorThread, self).start()
            return True
    
    def do_job(self, job):
        
        # Process Job 
        job_name = getattr(job, 'name', '<noname>')
        set_up = getattr(job, 'set_up', None)
        tear_down = getattr(job, 'tear_down', None)
        process = getattr(job, 'process', None)
        log.msg('processing job: %s' % job_name)
        
        if set_up is not None:
            try:
                set_up()
            except Exception as e:
                log.err(e, 'Exception in job set_up()')
        
        if process is not None:
            try:
                process()
            except Exception as e:
                log.err(e, 'Exception in job process()')
    
        if tear_down is not None:
            try:
                tear_down()
            except Exception as e:
                log.err(e, 'Exception in job tear_down()')
    
    def run(self):
        global _jobs
        log.msg('Supervisor thread started.')
        while self.running:
            job = _jobs.get()
            
            if job.runner is None:
                log.msg('doing job from supervisor thread')
                self.do_job(job)
            
            elif job.runner == SUPERVISOR_POOL:
                log.msg('doing job from supervisor thread pool')
                async_call(self.do_job)(job)
            
            elif job.runner == MODEL_POOL:
                log.msg('doing job from model thread pool')
                async_call_model(self.do_job)(job)
            
            elif job.runner == DOWNLOADER_POOL:
                log.msg('doing job from downloader thread pool')
                async_call_downloader(self.do_job)(job)
            
            
                    
        log.msg('Supervisor thread stopped.')
    
    def stop(self):
        global _jobs
        _jobs.put(StopSupervisorJob())
    
    def _exit_thread(self):
        self.running = False
    

class SupervisorService(service.Service):
    
    def __init__(self):
        global _supervisor
        global _pool
        global _model_pool
        global _downloader_pool
        
        if _supervisor is None:
            _supervisor = SupervisorThread()
        
        if _pool is None:
            _pool = threadpool.ThreadPool(minthreads=DEFAULT_POOL_SIZE/2, 
                                          maxthreads=DEFAULT_POOL_SIZE, 
                                          name='Supervisor Thread Pool')
            
        if _model_pool is None:
            _model_pool = threadpool.ThreadPool(minthreads=MODEL_POOL_SIZE/2, 
                                                maxthreads=MODEL_POOL_SIZE, 
                                                name='Model Thread Pool')
            
        if _downloader_pool is None:
            _downloader_pool = threadpool.ThreadPool(minthreads=DOWNLOADER_POOL_SIZE/2, 
                                                     maxthreads=DOWNLOADER_POOL_SIZE, 
                                                     name='Downloader Thread Pool')
            
        self.supervisor = _supervisor
        self.pool = _pool
        self.model_pool = _model_pool
        self.downloader_pool = _downloader_pool

    def startService(self):
        log.msg('Starting Supervisor service...')
        self.supervisor.start()
        self.pool.start()
        self.model_pool.start()
        self.downloader_pool.start()
        service.Service.startService(self)

    def stopService(self):
        log.msg('Stopping Supervisor service...')
        service.Service.stopService(self)
        self.downloader_pool.stop()
        self.model_pool.stop()
        self.pool.stop()
        self.supervisor.stop()


def async_call(function):
    '''call wrapped function asynchronously using supervisor thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool_lock
        global _pool
        with _pool_lock:
            _pool.callInThread(function, *args, **kwargs)
    return _async_call


def async_call_model(function):
    '''call wrapped function asynchronously using model thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _model_pool_lock
        global _model_pool
        with _model_pool_lock:
            _model_pool.callInThread(function, *args, **kwargs)
    return _async_call


def async_call_downloader(function):
    '''call wrapped function asynchronously using downloader thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _downloader_pool_lock
        global _downloader_pool
        with _downloader_pool_lock:
            _downloader_pool.callInThread(function, *args, **kwargs)
    return _async_call


@async_call           
def put_job(job):
    '''put job asynchronously using supervisor thread pool'''
    global _jobs
    _jobs.put(job)

