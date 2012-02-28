'''
Created on Feb 24, 2012

@author: arif
'''

import socket
import os
from os import path

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
        raise NotImplementedError()
    
    @property
    def ready(self):
        '''True if model environment is set up properly'''
        raise NotImplementedError()
