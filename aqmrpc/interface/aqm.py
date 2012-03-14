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
        
    def xmlrpc_setupenv(self, envid=None):
        ''' 
        Create a new modeling environment. 
        If envid is specified (integer), attempt to open existing id
        Return environment id on success, and None if failed
        '''
        log.msg('[rpc] wrf.setupenv() params: envid=%s' % envid)
        if envid is None:
            # create a new environment
            envdata = WRFEnvironment()
            envdata.save()
            envid = envdata.id
            result = wrfenv.setup(envid)
        else:
            # try to open existing environment
            try:
                envdata = WRFEnvironment.objects.get(id=envid)
            except WRFEnvironment.DoesNotExist:
                return None
            
            # create the environment if it is not there
            result = wrfenv.setup(envid)
            if (not result) and envdata.env_setup:
                # environment already exist
                return envid
                
        if result:
            envdata.env_setup = True
            envdata.save()
            return envid
        else:
            return None
    
    def xmlrpc_cleanupenv(self, envid):
        ''' Delete modeling environment. Return False on error '''
        log.msg('[rpc] wrf.cleanupenv() params: envid=%s' % envid)
        try:
            envdata = WRFEnvironment.objects.get(id=envid)
            envdata.env_setup = False
            envdata.save()
        except WRFEnvironment.DoesNotExist:
            return False
        wrfenv.cleanup(envid)
        return True
    
    def xmlrpc_set_namelist(self, envid, program, namelist_str):
        '''
        Set namelist file for coresponding program (WRF, WPS, ARWpost).
        This function will perform necessary replacement to fit the namelist 
        into specified modeling environment
        ''' 
        log.msg('[rpc] wrf.set_namelist() params: envid=%s program=%s' % (envid, program))
        
        program_list = ['WPS', 'WRF', 'ARWpost']
        if program not in program_list:
            raise Exception('Invalid Program')
        
        from aqmrpc.wrf.namelist import decode, encode
        
        parsed_namelist = decode.decode_namelist_string(namelist_str)
        if program == 'WPS':
            filepath = os.path.join(wrfenv.program_path(envid, program), 'namelist.wps')
            parsed_namelist['geogrid']['geog_data_path'][0] = wrfenv.get_geog_path()
        elif program == 'WRF':
            filepath = os.path.join(wrfenv.program_path(envid, program), 'namelist.input')
        elif program == 'ARWpost':
            filepath = os.path.join(wrfenv.program_path(envid, program), 'namelist.ARWpost')
            
        namelist_str_new = encode.encode_namelist(parsed_namelist)
        
        # save to file
        filepath = wrfenv.compute_path(envid, filepath)
        
        try:
            f = open(filepath, 'wb')
        except IOError:
            return None
            
        f.write(namelist_str_new)
        f.close()
    
    def xmlrpc_cleanup_wps(self, envid):
        ''' Remove temporary files from WPS working directory '''
        log.msg('[rpc] wrf.cleanup_wps() params: envid=%s' % envid)
        
        wps_dir = wrfenv.compute_path(envid, 'WPS')
        
        # cleanup gribfiles
        gribfiles = glob.glob(os.path.join(wps_dir, 'GRIBFILE.*'))
        for gribfile in gribfiles:
            os.remove(gribfile)
        
        # cleanup geogrid
        geo_ems = glob.glob(os.path.join(wps_dir, 'geo_em.*'))
        for geo_em in geo_ems:
            os.remove(geo_em)
        
        # cleanup ungrib
        ugfiles = glob.glob(os.path.join(wps_dir, 'FILE:*'))
        for ugfile in ugfiles:
            os.remove(ugfile)
        
        ugpfiles = glob.glob(os.path.join(wps_dir, 'PFILE:*'))
        for ugpfile in ugpfiles:
            os.remove(ugpfile)
        
        # cleanup metgrid
        # I don't think the metgrid files count as temporary files as we need
        # them when running wrf
#        met_ems = glob.glob(os.path.join(wps_dir, 'met_em.*'))
#        for met_em in met_ems:
#            os.remove(met_em)
    

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
        
    
    