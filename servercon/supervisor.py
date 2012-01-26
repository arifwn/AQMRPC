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

class Job():
    def __init__(self, target, data=None, onresult=None):
        self.target = target
        self.onresult = onresult
        self.data = data

class QuitNotification(Job):
    def __init__(self):
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
            # do something with the job...
        
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


def _put_job(job):
    global _jobs
    _jobs.put(job)

def put_job(job):
    # shouldn't block!
    global _pool
    _pool.callInThread(_put_job, job)

        