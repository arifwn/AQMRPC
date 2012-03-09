'''
Created on Jan 26, 2012

@author: arif
'''
import time
import xmlrpclib
from os import path

from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool

from aqmrpc.wrf import environment as wrfenv


class Interface(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
        self.server_handler = Server()
        self.putSubHandler('server', self.server_handler)
        
        self.job_handler = Job()
        self.putSubHandler('job', self.job_handler)
        
        self.task_handler = Task()
        self.putSubHandler('task', self.task_handler)
        
        self.filesystem_handler = Filesystem()
        self.putSubHandler('filesystem', self.filesystem_handler)


class Server(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_test_echo(self, s):
        return s
    

class Job(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
    def xmlrpc_create(self, config):
        return 'id'
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_test_echo(self, s):
        return s
    

class Task(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
    def xmlrpc_create(self, config):
        return 'id'
        
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_archive(self, id):
        return True
    
    def xmlrpc_remove(self, id):
        return True
    
    def xmlrpc_result(self, id):
        return {'result': True}
    
    def xmlrpc_test_echo(self, s):
        return s
    


class Filesystem(xmlrpc.XMLRPC):
    ''' access files in the modeling environment'''
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
        # whitelisted files
        self.files = {'WRF/namelist.input': 'WRF/namelist.input',
                      'WPS/namelist.wps': 'WPS/namelist.wps',
                      'ARWpost/namelist.ARWpost': 'ARWpost/namelist.ARWpost'}
    
    def verify_input(self, envid, targetpath):
        '''verify if input is actually valid'''
        try:
            p = self.files[targetpath]
        except KeyError:
            # not in whitelist, so it's not valid
            return False
        
        return wrfenv.verify_id(envid)
    
    def compute_path(self, envid, targetpath):
        '''compute the real absolute path from environmental id and target path'''
        return path.join(wrfenv.working_path(envid), self.files[targetpath])
    
    def xmlrpc_write(self, envid, targetpath, content):
        pass
        
    def xmlrpc_read(self, envid, targetpath):
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = self.compute_path(envid, targetpath)
        
        try:
            f = open(filepath, 'r')
        except IOError:
            return None
        data = f.read()
        f.close()
        return data
    
    def xmlrpc_stat(self, envid, targetpath):
        pass
    
    def xmlrpc_rm(self, envid, targetpath):
        pass
    
    