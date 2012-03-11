'''
Created on Jan 22, 2012

@author: arif
'''

from django.db import models

class WRFEnvironment(models.Model):
    running = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    
    env_setup = models.BooleanField(default=False)