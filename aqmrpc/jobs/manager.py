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
    