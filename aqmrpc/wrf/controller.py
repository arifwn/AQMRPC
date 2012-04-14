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
from aqmrpc.misc import interprocess_lock


class ModelEnvController(object):
    '''provides api to interact with modeling environment'''
    def __init__(self, envid):
        self.envid = str(envid)
        self.working_path = environment.working_path(self.envid)
        self.wps_path = environment.program_path(self.envid, 'WPS')
        self.wrf_path = environment.program_path(self.envid, 'WRF')
        self.arwpost_path = environment.program_path(self.envid, 'ARWpost')
        self.wpp_path = environment.program_path(self.envid, 'WPP')
        r_path = os.path.dirname(interprocess_lock.__file__) 
        self.runner_path = path.join(r_path, 'runner.py')
        
        # WRF Real
        self.wrf_real_socket_name = 'real_socket_ctrl'
        self.wrf_real_socket_path = path.join(self.wrf_path, self.wrf_real_socket_name)
        self.wrf_real_stdout_log = path.join(self.wrf_path, 'real_stdout.txt')
        self.wrf_real_stderr_log = path.join(self.wrf_path, 'real_stderr.txt')
        self.wrf_real_runner_log = path.join(self.wrf_path, 'real_runner_log.txt')
        self.wrf_real_pid_file = path.join(self.wrf_path, 'real_pid.txt')
        self.wrf_real_lock_file = path.join(self.wrf_path, 'real_lock.txt')
        
        # ARWpost
        self.arwpost_socket_name = 'arwpost_socket_ctrl'
        self.arwpost_socket_path = path.join(self.arwpost_path, self.arwpost_socket_name)
        self.arwpost_stdout_log = path.join(self.arwpost_path, 'arwpost_stdout.txt')
        self.arwpost_stderr_log = path.join(self.arwpost_path, 'arwpost_stderr.txt')
        self.arwpost_runner_log = path.join(self.arwpost_path, 'arwpost_runner_log.txt')
        self.arwpost_pid_file = path.join(self.arwpost_path, 'arwpost_pid.txt')
        self.arwpost_lock_file = path.join(self.arwpost_path, 'arwpost_lock.txt')
        
        # WRF
        self.wrf_socket_name = 'wrf_socket_ctrl'
        self.wrf_socket_path = path.join(self.wrf_path, self.wrf_socket_name)
        self.wrf_stdout_log = path.join(self.wrf_path, 'wrf_stdout.txt')
        self.wrf_stderr_log = path.join(self.wrf_path, 'wrf_stderr.txt')
        self.wrf_runner_log = path.join(self.wrf_path, 'wrf_runner_log.txt')
        self.wrf_pid_file = path.join(self.wrf_path, 'wrf_pid.txt')
        self.wrf_lock_file = path.join(self.wrf_path, 'wrf_lock.txt')
        
        # WPS UNGRIB
        self.wps_ungrib_socket_name = 'ungrib_socket_ctrl'
        self.wps_ungrib_socket_path = path.join(self.wps_path, self.wps_ungrib_socket_name)
        self.wps_ungrib_stdout_log = path.join(self.wps_path, 'ungrib_stdout.txt')
        self.wps_ungrib_stderr_log = path.join(self.wps_path, 'ungrib_stderr.txt')
        self.wps_ungrib_runner_log = path.join(self.wps_path, 'ungrib_runner_log.txt')
        self.wps_ungrib_log = path.join(self.wps_path, 'ungrib.log')
        self.wps_ungrib_pid_file = path.join(self.wps_path, 'ungrib_pid.txt')
        self.wps_ungrib_lock_file = path.join(self.wps_path, 'ungrib_lock.txt')
        
        # WPS GEOGRID
        self.wps_geogrid_socket_name = 'ungrib_socket_ctrl'
        self.wps_geogrid_socket_path = path.join(self.wps_path, self.wps_geogrid_socket_name)
        self.wps_geogrid_stdout_log = path.join(self.wps_path, 'geogrid_stdout.txt')
        self.wps_geogrid_stderr_log = path.join(self.wps_path, 'geogrid_stderr.txt')
        self.wps_geogrid_runner_log = path.join(self.wps_path, 'geogrid_runner_log.txt')
        self.wps_geogrid_log = path.join(self.wps_path, 'geogrid.log')
        self.wps_geogrid_pid_file = path.join(self.wps_path, 'geogrid_pid.txt')
        self.wps_geogrid_lock_file = path.join(self.wps_path, 'geogrid_lock.txt')
        
        # WPS METGRID
        self.wps_metgrid_socket_name = 'metgrid_socket_ctrl'
        self.wps_metgrid_socket_path = path.join(self.wps_path, self.wps_metgrid_socket_name)
        self.wps_metgrid_stdout_log = path.join(self.wps_path, 'metgrid_stdout.txt')
        self.wps_metgrid_stderr_log = path.join(self.wps_path, 'metgrid_stderr.txt')
        self.wps_metgrid_runner_log = path.join(self.wps_path, 'metgrid_runner_log.txt')
        self.wps_metgrid_log = path.join(self.wps_path, 'metgrid.log')
        self.wps_metgrid_pid_file = path.join(self.wps_path, 'metgrid_pid.txt')
        self.wps_metgrid_lock_file = path.join(self.wps_path, 'metgrid_lock.txt')
    
    def wait(self, socket_path):
        '''wait until runner finished'''
        controller = Controller(socket_path)
        for i in range(10):
            if controller.connect():
                # now wait until runner finished
                controller.wait()
                break
            else:
                time.sleep(1)
    
    def run(self, **kwargs):
        subprocess.call([settings.AQM_PYTHON_BIN, self.runner_path, 
                         '--rundir', kwargs['rundir'],
                         '--target', kwargs['target'],
                         '--socket', kwargs['socket'],
                         '--stdout', kwargs['stdout'],
                         '--stderr', kwargs['stderr'],
                         '--runnerlog', kwargs['runnerlog'],
                         '--pidfile', kwargs['pidfile'],
                         '--lockfile', kwargs['lockfile'],
                         '--id', kwargs['id']])
        
        # acquire lock
        lock = interprocess_lock.FLockRLock(open(kwargs['lockfile'], 'a'))
        lock.acquire()
        # runner is now running
        lock.release()
        
        self.wait(kwargs['socket'])
        
        # sleep for a while to make sure files opened by runner
        # has been closed properly
        time.sleep(1)
    
    def terminate(self, socket_path):
        ''' Terminate a Runner. '''
        c = Controller(socket_path)
        if c.connect():
            c.terminate()
    
    def resume(self, socket_path):
        ''' Resume wait for the specified runner. '''
        self.wait(socket_path)
        
        # sleep for a while to make sure files opened by runner
        # has been closed properly
        time.sleep(5)
    
    
    def run_wrf_real(self):
        '''
        Run real and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.wrf_path, 
                 target='./real.exe', 
                 socket=self.wrf_real_socket_path,
                 stdout=self.wrf_real_stdout_log, 
                 stderr=self.wrf_real_stderr_log,
                 runnerlog=self.wrf_real_runner_log,
                 pidfile=self.wrf_real_pid_file,
                 lockfile=self.wrf_real_lock_file,
                 id='real')
        
        return self.check_wrf_real_result()
    
    def resume_wrf_real(self):
        '''
        Reconnect to running wrf real.exe session.
        Return True if wrf finished successfully, and False if otherwise
        '''
        self.resume(self.wrf_real_socket_path)
        return self.check_wrf_real_result()
    
    def terminate_wrf_real(self):
        self.terminate(self.wrf_real_socket_path)
    
    def wrf_real_is_running(self):
        '''check whether real.exe job is running by checking the pid file'''
        return check_pidfile(self.wrf_real_pid_file)
    
    def check_wrf_real_result(self):
        '''check whether real.exe run successfully'''
        tag = 'SUCCESS COMPLETE REAL_EM INIT'
        with open(self.wrf_real_stdout_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    
    def run_wrf(self):
        '''
        Run wrf and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.wrf_path, 
                 target='./wrf.exe', 
                 socket=self.wrf_socket_path,
                 stdout=self.wrf_stdout_log, 
                 stderr=self.wrf_stderr_log,
                 runnerlog=self.wrf_runner_log,
                 pidfile=self.wrf_pid_file,
                 lockfile=self.wrf_lock_file,
                 id='wrf')
        
        return self.check_wrf_result()
    
    def resume_wrf(self):
        '''
        Reconnect to running wrf session.
        Return True if wrf finished successfully, and False if otherwise
        '''
        self.resume(self.wrf_socket_path)
        return self.check_wrf_result()
    
    def terminate_wrf(self):
        self.terminate(self.wrf_socket_path)
        
    def wrf_is_running(self):
        '''check whether wrf job is running by checking the pid file'''
        return check_pidfile(self.wrf_pid_file)
    
    def check_wrf_result(self):
        '''check whether wrf run successfully'''
        tag = 'SUCCESS COMPLETE WRF'
        with open(self.wrf_stdout_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def run_wps_ungrib(self):
        '''
        Run ungrib and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.wps_path, 
                 target='./ungrib.exe', 
                 socket=self.wps_ungrib_socket_path,
                 stdout=self.wps_ungrib_stdout_log, 
                 stderr=self.wps_ungrib_stderr_log,
                 runnerlog=self.wps_ungrib_runner_log,
                 pidfile=self.wps_ungrib_pid_file,
                 lockfile=self.wps_ungrib_lock_file,
                 id='ungrib')
        
        return self.check_wps_ungrib_result()
    
    def resume_wps_ungrib(self):
        '''
        Reconnect to running wps ungrib session.
        Return True if wps ungrib finished successfully, and False if otherwise
        '''
        self.resume(self.wps_ungrib_socket_path)
        return self.check_wps_ungrib_result()
        
    def terminate_wps_ungrib(self):
        self.terminate(self.wps_ungrib_socket_path)
        
    def wps_ungrib_is_running(self):
        '''check whether ungrib job is running by checking the pid file'''
        return check_pidfile(self.wps_ungrib_pid_file)
    
    def check_wps_ungrib_result(self):
        '''check whether ungrib run successfully'''
        tag = '*** Successful completion of program ungrib.exe ***'
        with open(self.wps_ungrib_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def run_wps_geogrid(self):
        '''
        Run geogrid and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.wps_path, 
                 target='./geogrid.exe', 
                 socket=self.wps_geogrid_socket_path,
                 stdout=self.wps_geogrid_stdout_log, 
                 stderr=self.wps_geogrid_stderr_log,
                 runnerlog=self.wps_geogrid_runner_log,
                 pidfile=self.wps_geogrid_pid_file,
                 lockfile=self.wps_geogrid_lock_file,
                 id='geogrid')
        
        return self.check_wps_geogrid_result()
    
    def resume_wps_geogrid(self):
        '''
        Reconnect to running wps geogrid session.
        Return True if wps geogrid finished successfully, and False if otherwise
        '''
        self.resume(self.wps_geogrid_socket_path)
        return self.check_wps_geogrid_result()
        
    def terminate_wps_geogrid(self):
        self.terminate(self.wps_geogrid_socket_path)
        
    def wps_geogrid_is_running(self):
        '''check whether geogrid job is running by checking the pid file'''
        return check_pidfile(self.wps_ungrib_pid_file)
    
    def check_wps_geogrid_result(self):
        '''check whether geogrid run successfully'''
        tag = '*** Successful completion of program geogrid.exe ***'
        with open(self.wps_geogrid_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def run_wps_metgrid(self):
        '''
        Run metgrid and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.wps_path, 
                 target='./metgrid.exe', 
                 socket=self.wps_metgrid_socket_path,
                 stdout=self.wps_metgrid_stdout_log, 
                 stderr=self.wps_metgrid_stderr_log,
                 runnerlog=self.wps_metgrid_runner_log,
                 pidfile=self.wps_metgrid_pid_file,
                 lockfile=self.wps_metgrid_lock_file,
                 id='metgrid')
        
        return self.check_wps_metgrid_result()
    
    def resume_wps_metgrid(self):
        '''
        Reconnect to running wps metgrid session.
        Return True if wps metgrid finished successfully, and False if otherwise
        '''
        self.resume(self.wps_metgrid_socket_path)
        return self.check_wps_metgrid_result()
        
    def terminate_wps_metgrid(self):
        self.terminate(self.wps_metgrid_socket_path)
        
    def wps_metgrid_is_running(self):
        '''check whether metgrid job is running by checking the pid file'''
        return check_pidfile(self.wps_metgrid_pid_file)
    
    def check_wps_metgrid_result(self):
        '''check metgrid metgrid run successfully'''
        tag = '*** Successful completion of program metgrid.exe ***'
        with open(self.wps_metgrid_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def run_arwpost(self):
        '''
        Run ARWpost and wait until its completion.
        Return True if wrf finished successfully, and False if otherwise
        '''
        
        self.run(rundir=self.arwpost_path, 
                 target='./ARWpost.exe', 
                 socket=self.arwpost_socket_path,
                 stdout=self.arwpost_stdout_log, 
                 stderr=self.arwpost_stderr_log,
                 runnerlog=self.arwpost_runner_log,
                 pidfile=self.arwpost_pid_file,
                 lockfile=self.arwpost_lock_file,
                 id='arwpost')
        
        return self.check_arwpost_result()
    
    def resume_arwpost(self):
        '''
        Reconnect to running arwpost session.
        Return True if arwpost finished successfully, and False if otherwise
        '''
        self.resume(self.arwpost_socket_path)
        return self.check_arwpost_result()
        
    def terminate_arwpost(self):
        self.terminate(self.arwpost_socket_path)
        
    def wps_arwpost_is_running(self):
        '''check whether ARWpost job is running by checking the pid file'''
        return check_pidfile(self.arwpost_pid_file)
    
    def check_arwpost_result(self):
        '''check ARWpost run successfully'''
        tag = '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!  Successful completion of ARWpost  !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
        with open(self.arwpost_stdout_log, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag.strip():
                return True
        return False
    

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
    
    def terminate(self):
        ''' Send Terminate command. '''
        self.send_command('terminate')
    
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
    