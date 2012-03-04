'''
Created on Feb 24, 2012

@author: arif
'''

import socket
import os
import json
import subprocess
import time
from os import path

import environment
from aqmrpc import settings


class ModelEnvController(object):
    
    def __init__(self, id):
        self.id = id
        self.working_path = environment.working_path(id)
        self.wps_path = path.join(self.working_path, 'WPS/')
        self.wrf_path = path.join(self.working_path, 'WRF/')
        self.arwpost_path = path.join(self.working_path, 'ARWpost/')
        self.wpp_path = path.join(self.working_path, 'WPP/')
#        r_path, mdl = path.split(environment.__file__)
        r_path = os.path.dirname(__file__) 
        self.runner_path = path.join(r_path, 'runner.py')
    
    def run_wrf(self):
        socket_ctrl = path.join(self.wrf_path, 'socket_ctrl')
        try:
            os.remove(socket_ctrl)
        except OSError:
            pass
        
        subprocess.call([settings.AQM_PYTHON_BIN, self.runner_path, 
                         '--rundir', self.wrf_path,
                         '--target', './wrf.exe',
                         '--id', 'wrf'])
        

class Controller(object):
    
    def __init__(self, target_path):
        self.socket_path = path.join(target_path, 'socket_ctrl')
    
    def connect(self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)
        
    def send_command(self, command):
        self.socket.send(command)
        return self.socket.recv(1024)
    
    def close(self):
        try:
            self.socket.close()
        except:
            pass
    
    def __del__(self):
        self.close()
    
    @property
    def status(self):
        '''return running status of the model environment'''
        try:
            stat = json.loads(self.send_command('status'))
        except:
            stat = None
        return stat
    