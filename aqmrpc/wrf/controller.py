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
        r_path = os.path.dirname(__file__) 
        self.runner_path = path.join(r_path, 'runner.py')
        
        self.wrf_socket_name = 'wrf_socket_ctrl'
        self.wrf_socket_path = path.join(self.wrf_path, self.wrf_socket_name)
        self.wrf_stdout_log = path.join(self.wrf_path, 'wrf_stdout.txt')
        self.wrf_stderr_log = path.join(self.wrf_path, 'wrf_stderr.txt')
        self.wrf_runner_log = path.join(self.wrf_path, 'wrf_runner_log.txt')
        self.wrf_pid_file = path.join(self.wrf_path, 'wrf_pid.txt')
    
    def wait(self, socket_path):
        '''wait until runner finished'''
        controller = Controller(socket_path)
        for i in range(5):
            if controller.connect():
                # now wait until runner finished
                controller.wait()
                break
            time.sleep(0.5)
    
    def check_wrf_result(self):
        '''check whether wrf run successfully'''
        return False
    
    def run_wrf(self):
        '''
        Run wrf and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        subprocess.call([settings.AQM_PYTHON_BIN, self.runner_path, 
                         '--rundir', self.wrf_path,
                         '--target', './wrf.exe',
                         '--socket', self.wrf_socket_path,
                         '--stdout', self.wrf_stdout_log,
                         '--stderr', self.wrf_stderr_log,
                         '--runnerlog', self.wrf_runner_log,
                         '--pidfile', self.wrf_pid_file,
                         '--id', 'wrf'])
        
        self.wait(self.wrf_socket_path)
        return self.check_wrf_result()
    
    def wrf_is_running(self):
        '''check whether wrf job is running by checking the pid file'''
        return check_pidfile(self.wrf_pid_file)
        

class Controller(object):
    '''provides api to interact with runner'''
    def __init__(self, socket_path):
        self.socket_path = socket_path
    
    def connect(self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        for i in range(5):
            try:
                self.socket.connect(self.socket_path)
                return True
            except:
                pass
        return False
        
    def send_command(self, command):
        self.socket.send(command)
        return self.socket.recv(1024)
    
    def close(self):
        try:
            self.socket.close()
        except:
            pass
    
    def wait(self):
        '''wait until the other end close the socket'''
        self.send_command('wait')
    
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


def check_pid(pid):
    '''check whether a process with given pid is running'''
    process_list = [(int(p), c) for p, c in [x.rstrip('\n').split(' ', 1) for x in os.popen('ps h -eo pid:1,command')]]
    running = False
    for target_pid in process_list:
        if target_pid[0] == pid:
            # target pid is exist
            running = True
            break
    return running

def check_pidfile(pidfilepath):
    '''
    get pid from given pid file and check whether a process with given 
    pid is running
    '''
    try:
        pidfile = open(pidfilepath, 'r')
    except IOError:
        # no pidfile, so wrf is not running
        return False
    
    try:
        target_pid = int(pidfile.read())
    except ValueError:
        # invalid pidfile?
        return False
    
    pidfile.close()
    
    return check_pid(target_pid)
    