'''
Created on Jan 26, 2012

@author: arif
'''
import threading
from twisted.python import log, threadpool
import Queue

_supervisor = None
_pool = threadpool.ThreadPool()
_jobs = Queue.Queue()

class Job():
    def __init__(self, target, data=None, onresult=None):
        self.target = target
        self.onresult = onresult
        self.data = data

class SupervisorThread(threading.Thread):
    
    daemon = True
    running = False
    jobs = _jobs
    
    def start(self):
        self.running = True
        super(SupervisorThread, self).start()
        
    def run(self):
        while self.running:
            job = self.jobs.get()
            # do something with the job...

def _put_job(job):
    _jobs.put(job)

def put_job(job):
    # shouldn't block!
    _pool.callInThread(_put_job, job)

def init():
    '''Initialize Supervisor Thread
    '''
    if _supervisor is None:
        log.msg('Initializing Supervisor...')
        _supervisor = SupervisorThread()
        _supervisor.start()
    