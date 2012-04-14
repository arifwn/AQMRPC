'''
Created on Jan 30, 2012

@author: arif
'''
from django.conf import settings

JOB_COUNT = 0

def get_job_count():
    global JOB_COUNT
    return JOB_COUNT

def get_job_capacity():
    max_job = getattr(settings, 'THREAD_POOL_CPUBOUND_SIZE', 2)
    return max_job

def increment_job():
    global JOB_COUNT
    JOB_COUNT += 1
    
def decrement_job():
    global JOB_COUNT
    JOB_COUNT -= 1

def stop_wrf_job(envid):
    ''' Stop any wrf job associated with supplied env id. '''
    from aqmrpc.wrf import environment as wrfenv
    from aqmrpc.models import CurrentJob
    from twisted.python import log
    
    log.msg('Stopping WRF Job with envid %s' % (envid))
    
    # remove the job entry
    try:
        jobentry = CurrentJob.objects.get(envid=envid)
    except CurrentJob.DoesNotExist:
        # job does not exist, probably canceled
        return
    
    jobentry.delete()
    
    # terminate all running process associated with the job
    
    e = wrfenv.Env(envid)
    e.stop_wps()
    e.stop_wrf()
    e.stop_arwpost()
    