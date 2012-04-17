'''
Created on Jan 26, 2012

@author: arif
'''
import threading

from twisted.application import service
from twisted.python import log, threadpool
from django.conf import settings
from rest import client

import Queue

DEBUG = getattr(settings, 'DEBUG', True)

RUNNER_BLOCKING = 0
RUNNER_SUPERVISOR = 1
RUNNER_CPUBOUND = 2
RUNNER_NETBOUND = 4
RUNNER_IOBOUND = 8

TPSIZE_DEFAULT = getattr(settings, 'THREAD_POOL_DEFAULT_SIZE', 20)
TPSIZE_CPUBOUND = getattr(settings, 'THREAD_POOL_CPUBOUND_SIZE', 10)
TPSIZE_NETBOUND = getattr(settings, 'THREAD_POOL_NETBOUND_SIZE', 10)
TPSIZE_IOBOUND = getattr(settings, 'THREAD_POOL_IOBOUND_SIZE', 10)

_supervisor = None

# supervisor thread pool
_pool_supervisor = None
_pool_supervisor_lock = threading.RLock()

# cpu-bound thread pool
_pool_cpubound = None
_pool_cpubound_lock = threading.RLock()

# network-bound thread pool
_pool_netbound = None
_pool_netbound_lock = threading.RLock()

# io-bound thread pool
_pool_iobound = None
_pool_iobound_lock = threading.RLock()

_jobs = Queue.Queue()


class BaseJob(object):
    
    def __init__(self, name=None, runner=RUNNER_BLOCKING, callback=None):
        self.name = name
        self.runner = runner
        self.callback_func = None
        self.results = {}
    
    def set_up(self):
        return True
    
    def process(self):
        raise NotImplementedError()
    
    def callback(self):
        if self.callback_func is None:
            return
        
        try:
            self.callback_func(**self.results)
        except Exception as e:
            log.msg('[%s] callback exception: %s' % (self.__class__.name, e))
            
    
    def tear_down(self):
        pass


class StopSupervisorJob(BaseJob):
    
    def __init__(self, name='Stop Supervisor', runner=RUNNER_BLOCKING, callback=None):
        super(StopSupervisorJob, self).__init__(name=name, runner=runner, callback=callback)
    
    def process(self):
        global _supervisor
        _supervisor._exit_thread()


class Callback(object):
    
    def __call__(self, **kwargs):
        raise NotImplementedError


class RESTCallback(Callback):
    
    def __init__(self, base_url, resource, method='get', username=None, password=None):
        self.base_url = base_url
        self.resource = resource
        self.username = username
        self.password = password
        self.method = method
        
    def __call__(self, **kwargs):
        self.conn = client.Connection(self.base_url, self.username, self.password)
        return self.conn.request(self.resource, self.method, kwargs.items(), headers={})


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
        callback = getattr(job, 'callback', None)
        log.msg('[runner] processing job: %s <%s>' % (job_name, job.__class__.__name__))
        
        if set_up is not None:
            is_continue = False
            try:
                is_continue = set_up()
            except Exception as e:
                log.err(e, '[runner] Exception in job set_up()')
        
        if (process is not None) and is_continue:
            try:
                process()
            except Exception as e:
                log.err(e, '[runner] Exception in job process()')
        
        if callback is not None:
            try:
                callback()
            except Exception as e:
                log.err(e, '[runner] Exception in job callback()')
        
    
        if tear_down is not None:
            try:
                tear_down()
            except Exception as e:
                log.err(e, '[runner] Exception in job tear_down()')
    
    def run(self):
        global _jobs
        log.msg('[supervisor] Supervisor thread started.')
        while self.running:
            log.msg('[supervisor] waiting for job...')
            job = _jobs.get()
            log.msg('[supervisor] received new job: %s' % job.__class__.__name__)
            
            if job.runner == RUNNER_BLOCKING:
                log.msg('[supervisor] doing job from supervisor thread')
                self.do_job(job)
            
            elif job.runner == RUNNER_SUPERVISOR:
                log.msg('[supervisor] doing job from supervisor thread pool')
                async_call(self.do_job)(job)
            
            elif job.runner == RUNNER_CPUBOUND:
                log.msg('[supervisor] doing job from cpu-bound thread pool')
                async_call_cpubound(self.do_job)(job)
            
            elif job.runner == RUNNER_NETBOUND:
                log.msg('[supervisor] doing job from network-bound thread pool')
                async_call_netbound(self.do_job)(job)
                
            elif job.runner == RUNNER_IOBOUND:
                log.msg('[supervisor] doing job from io-bound thread pool')
                async_call_iobound(self.do_job)(job)
            
                    
        log.msg('[supervisor] Supervisor thread stopped')
    
    def stop(self):
        global _jobs
        _jobs.put(StopSupervisorJob())
    
    def _exit_thread(self):
        self.running = False
    

class SupervisorService(service.Service):
    
    def __init__(self):
        global _supervisor
        global _pool_supervisor
        global _pool_cpubound
        global _pool_netbound
        global _pool_iobound
        
        if _supervisor is None:
            _supervisor = SupervisorThread()
        
        if _pool_supervisor is None:
            _pool_supervisor = threadpool.ThreadPool(minthreads=TPSIZE_DEFAULT/2, 
                                          maxthreads=TPSIZE_DEFAULT, 
                                          name='Supervisor Thread Pool')
            
        if _pool_cpubound is None:
            _pool_cpubound = threadpool.ThreadPool(minthreads=TPSIZE_CPUBOUND/2, 
                                                maxthreads=TPSIZE_CPUBOUND, 
                                                name='CPU-Bound Thread Pool')
            
        if _pool_netbound is None:
            _pool_netbound = threadpool.ThreadPool(minthreads=TPSIZE_NETBOUND/2, 
                                                     maxthreads=TPSIZE_NETBOUND, 
                                                     name='Network-Bound Thread Pool')
            
        if _pool_iobound is None:
            _pool_iobound = threadpool.ThreadPool(minthreads=TPSIZE_IOBOUND/2, 
                                                     maxthreads=TPSIZE_IOBOUND, 
                                                     name='IO-Bound Thread Pool')
            
        self.supervisor = _supervisor
        self.pool_supervisor = _pool_supervisor
        self.pool_cpubound = _pool_cpubound
        self.pool_netbound = _pool_netbound
        self.pool_iobound = _pool_iobound

    def startService(self):
        log.msg('[supervisor service] Starting...')
        self.supervisor.start()
        self.pool_supervisor.start()
        self.pool_cpubound.start()
        self.pool_netbound.start()
        self.pool_iobound.start()
        service.Service.startService(self)

    def stopService(self):
        log.msg('[supervisor service] Stopping...')
        service.Service.stopService(self)
        self.pool_iobound.stop()
        self.pool_netbound.stop()
        self.pool_cpubound.stop()
        self.pool_supervisor.stop()
        self.supervisor.stop()


def async_call(function):
    '''call wrapped function asynchronously using supervisor thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool_supervisor_lock
        global _pool_supervisor
        with _pool_supervisor_lock:
            _pool_supervisor.callInThread(function, *args, **kwargs)
    return _async_call


def async_call_cpubound(function):
    '''call wrapped function asynchronously using cpu-bound thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool_cpubound_lock
        global _pool_cpubound
        with _pool_cpubound_lock:
            _pool_cpubound.callInThread(function, *args, **kwargs)
    return _async_call


def async_call_netbound(function):
    '''call wrapped function asynchronously using network-bound thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool_netbound_lock
        global _pool_netbound
        with _pool_netbound_lock:
            _pool_netbound.callInThread(function, *args, **kwargs)
    return _async_call


def async_call_iobound(function):
    '''call wrapped function asynchronously using io-bound thread pool
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool_iobound_lock
        global _pool_iobound
        with _pool_iobound_lock:
            _pool_iobound.callInThread(function, *args, **kwargs)
    return _async_call



@async_call           
def put_job(job):
    '''put job asynchronously using supervisor thread pool'''
    global _jobs
    _jobs.put(job)

