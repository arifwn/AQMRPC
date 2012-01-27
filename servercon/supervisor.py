'''
Created on Jan 26, 2012

@author: arif
'''
import threading

from twisted.application import service
from twisted.python import log, threadpool

import Queue


_supervisor = None
_pool = None
_jobs = Queue.Queue()


class Job(object):
    
    def __init__(self, name=None):
        if name is None:
            self.name = 'Job'
        else:
            self.name = name
    
    def set_up(self):
        pass
    
    def process(self):
        raise NotImplementedError()
    
    def tear_down(self):
        pass


class QuitNotification(Job):
    
    def __init__(self):
        super(QuitNotification, self).__init__('Notify Supervisor to quit')
    
    def process(self):
        pass


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
        
    def run(self):
        global _jobs
        log.msg('Supervisor thread started.')
        while self.running:
            job = _jobs.get()
            if isinstance(job, QuitNotification):
                break
            
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
                    
        log.msg('Supervisor thread stopped.')
    
    def stop(self):
        global _jobs
        _jobs.put(QuitNotification())
        self.running = False
    

class SupervisorService(service.Service):
    
    def __init__(self):
        global _supervisor
        global _pool
        
        if _supervisor is None:
            _supervisor = SupervisorThread()
        
        if _pool is None:
            _pool = threadpool.ThreadPool()
        
        self.supervisor = _supervisor
        self.pool = _pool

    def startService(self):
        log.msg('Starting Supervisor service...')
        service.Service.startService(self)
        self.supervisor.start()
        self.pool.start()

    def stopService(self):
        log.msg('Stopping Supervisor service...')
        service.Service.stopService(self)
        self.pool.stop()
        self.supervisor.stop()


def async_call(function):
    '''call wrapped function asyncrously in another thread
    
    It doesn't wait until the thread finished and return
    immediately (fire and forget).
    
    '''
    def _async_call(*args, **kwargs):
        global _pool
        return _pool.callInThread(function, *args, **kwargs)
    
    return _async_call


@async_call
def put_job(job):
    global _jobs
    _jobs.put(job)

