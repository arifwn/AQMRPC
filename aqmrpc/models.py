'''
Created on Jan 22, 2012

@author: arif
'''

from django.db import models

class WRFEnvironment(models.Model):
    # last step that successfully run
    last_step = models.TextField(blank=True)
    
    # current step
    current_step = models.TextField(blank=True)
    
    # is current step is running?
    running = models.BooleanField(default=False)
    
    # is current step is in error state?
    error = models.BooleanField(default=False)
    
    # is modeling environment is setup correctly?
    env_setup = models.BooleanField(default=False)

    def reset(self):
        ''' reset all state '''
        self.last_step = ''
        self.current_step = ''
        self.running = False
        self.error = False
        self.env_setup = False


class CurrentJob(models.Model):
    name = models.TextField()
    job_type = models.TextField(db_index=True)
    envid = models.IntegerField(db_index=True)
    step = models.TextField(blank=True)
