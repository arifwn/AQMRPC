'''
Created on Jan 26, 2012

@author: arif
'''
import time
import xmlrpclib
import os
from os import path

from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool

from aqmrpc.wrf import environment as wrfenv
from aqmrpc.models import WRFEnvironment
from aqmrpc.misc import filesystem
from aqmrpc import settings as aqmsettings


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
        
        self.wrf_handler = WRF()
        self.putSubHandler('wrf', self.wrf_handler)


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
    
    
class WRF(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
    def xmlrpc_setupenv(self):
        envdata = WRFEnvironment()
        envdata.save()
        envid = str(envdata.id)
        result = wrfenv.setup(envid)
        if result:
            envdata.env_setup = True
            envdata.save()
            return envid
        else:
            return None
    
    def xmlrpc_cleanupenv(self, envid):
        try:
            envdata = WRFEnvironment.objects.get(id=int(envid))
            envdata.env_setup = False
            envdata.save()
        except WRFEnvironment.DoesNotExist:
            return False
        wrfenv.cleanup(envid)
        return True


class Job(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, envid):
        return []
    
    def xmlrpc_info(self, envid):
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
        self.files = {
                      'WRF/namelist.input': 'WRF/namelist.input',
                      'WPS/namelist.wps': 'WPS/namelist.wps',
                      'ARWpost/namelist.ARWpost': 'ARWpost/namelist.ARWpost',
        }
    
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
        '''
        replace content in the target file.
        create new file if not exist.
        try to wrap content in xmlrpclib.Binary especially for binary content. 
        '''
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = self.compute_path(envid, targetpath)
        
        try:
            f = open(filepath, 'wb')
        except IOError:
            return None
        
        if isinstance(content, xmlrpclib.Binary):
            data = content.data
        else:
            data = content
            
        f.write(data)
        f.close()
        
    def xmlrpc_read(self, envid, targetpath):
        '''
        return content of target file.
        target file is treated as binary data (xmlrpclib.Binary)
        '''
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = self.compute_path(envid, targetpath)
        
        try:
            f = open(filepath, 'rb')
        except IOError:
            return None
        data = f.read()
        f.close()
        return xmlrpclib.Binary(data)
    
    def xmlrpc_exist(self, envid, targetpath):
        '''verify if file really exist'''
        if self.verify_input(envid, targetpath) is False:
            return False
        filepath = self.compute_path(envid, targetpath)
        
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False
    
    def xmlrpc_remove(self, envid, targetpath):
        '''remove target file'''
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = self.compute_path(envid, targetpath)
        
        try:
            os.remove(filepath)
        except OSError:
            return
        
    
    