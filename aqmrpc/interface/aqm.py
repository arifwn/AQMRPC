'''
Created on Jan 26, 2012

@author: arif
'''
import time
import xmlrpclib
import os
import os.path
import glob

from twisted.web import xmlrpc
from twisted.python import log

from aqmrpc.wrf import environment as wrfenv
from aqmrpc.models import WRFEnvironment
from aqmrpc.misc import filesystem
from aqmrpc.jobs import manager as jobmanager
from servercon import supervisor
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
    
    def xmlrpc_utilization(self):
        import psutil
        import random
        data = {}
        data['cpu'] = psutil.cpu_percent()
        mem = psutil.phymem_usage()
        
        # xmlrpc doesn't support long int, so return data as float
        data['memory_used'] = mem.percent / 100.0 * mem.total
        data['memory_total'] = float(mem.total)
        data['memory_percent'] = mem.percent
        
        disk = psutil.disk_usage(aqmsettings.AQM_WORKING_DIR)
        
        data['disk_used'] = float(disk.used)
        data['disk_total'] = float(disk.total)
        data['disk_percent'] = disk.percent
        
        # get job slot status
        data['slot_used'] = float(jobmanager.get_job_count())
        data['slot_total'] = float(jobmanager.get_job_capacity())
        
        return data
    
    def xmlrpc_test_echo(self, s):
        return s
    
    
class WRF(xmlrpc.XMLRPC):
    
    def __init__(self, allowNone=True, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
    
    def xmlrpc_add_job(self, data, envid=None):
        from aqmrpc.wrf.job import WRFRun
        j = WRFRun(data=data, envid=envid)
        supervisor.put_job(j)
        return True
        
    def xmlrpc_setupenv(self, envid=None):
        ''' 
        Create a new modeling environment. 
        If envid is specified (integer), attempt to open existing id
        Return environment id on success, and None if failed
        '''
        log.msg('[rpc] wrf.setupenv() params: envid=%s' % envid)
        
        try:
            env = wrfenv.Env(envid)
        except wrfenv.Env.DoesNotExist:
            return None
        
        env.setup()
        return env.envid
    
    def xmlrpc_cleanupenv(self, envid):
        ''' Delete modeling environment. Return False on error '''
        log.msg('[rpc] wrf.cleanupenv() params: envid=%s' % envid)
        if envid is None:
            raise Exception('envid cannot be None!')
        
        try:
            env = wrfenv.Env(envid)
        except wrfenv.Env.DoesNotExist:
            return False
        
        env.cleanup()
        return True
    
    def xmlrpc_set_namelist(self, envid, program, namelist_str):
        '''
        Set namelist file for coresponding program (WRF, WPS, ARWpost).
        This function will perform necessary replacement to fit the namelist 
        into specified modeling environment
        ''' 
        log.msg('[rpc] wrf.set_namelist() params: envid=%s program=%s' % (envid, program))
        if envid is None:
            raise Exception('envid cannot be None!')
        
        env = wrfenv.Env(envid)
        env.set_namelist(program, namelist_str)
        
    
    def xmlrpc_cleanup_wps(self, envid):
        ''' Remove temporary files from WPS working directory '''
        log.msg('[rpc] wrf.cleanup_wps() params: envid=%s' % envid)
        if envid is None:
            raise Exception('envid cannot be None!')
        
        env = wrfenv.Env(envid)
        env.cleanup_wps()
        
    

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
    
    def verify_input(self, envid, targetpath):
        '''verify if input is actually valid'''
        
        if wrfenv.verify_id(envid):
            return filesystem.path_inside(wrfenv.working_path(envid), wrfenv.compute_path(envid, targetpath))
        else:
            return False
    
    def xmlrpc_write(self, envid, targetpath, content):
        '''
        replace content in the target file.
        create new file if not exist.
        try to wrap content in xmlrpclib.Binary especially for binary content. 
        '''
        log.msg('[rpc] filesystem.write() params: envid=%s targetpath=%s' % (envid, targetpath))
        
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = wrfenv.compute_path(envid, targetpath)
        
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
        log.msg('[rpc] filesystem.read() params: envid=%s targetpath=%s' % (envid, targetpath))
        
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = wrfenv.compute_path(envid, targetpath)
        
        try:
            f = open(filepath, 'rb')
        except IOError:
            return None
        data = f.read()
        f.close()
        return xmlrpclib.Binary(data)
    
    def xmlrpc_exist(self, envid, targetpath):
        '''verify if file really exist'''
        log.msg('[rpc] filesystem.exist() params: envid=%s targetpath=%s' % (envid, targetpath))
        
        if self.verify_input(envid, targetpath) is False:
            return False
        filepath = wrfenv.compute_path(envid, targetpath)
        
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False
    
    def xmlrpc_remove(self, envid, targetpath):
        '''remove target file'''
        log.msg('[rpc] filesystem.remove() params: envid=%s targetpath=%s' % (envid, targetpath))
        
        if self.verify_input(envid, targetpath) is False:
            return None
        filepath = wrfenv.compute_path(envid, targetpath)
        
        try:
            os.remove(filepath)
        except OSError:
            return
        
    
    