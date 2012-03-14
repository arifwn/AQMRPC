'''
Created on Feb 24, 2012

@author: arif
'''

import os
from os import path
import shutil

from aqmrpc import settings
from aqmrpc.models import WRFEnvironment


class EnvironmentNotSetup(Exception):
    pass


class Env(object):
    ''' Provides access to modeling environment '''
    
    DoesNotExist = WRFEnvironment.DoesNotExist
    
    def __init__(self, envid=None):
        if envid is None:
            self.envdata = WRFEnvironment()
            self.envdata.save()
            self.envid = self.envdata.id
        else:
            self.envid = envid
            self.envdata = WRFEnvironment.objects.get(id=self.envid)
    
    def save(self):
        '''Save WRFEnvironment instance'''
        self.envdata.save()
    
    def verify(self):
        '''Check if this environment is actually valid and exist.'''
        return verify_id(self.envid)
    
    def setup(self):
        '''
        Create a new modeling environment in AQM_WORKING_DIR location.
        Return model working path.
        '''
        result = setup(self.envid)
        if result:
            self.envdata.env_setup = True
            self.envdata.save
        return result
    
    def cleanup(self):
        '''Remove a modeling environment identified with id.'''
        cleanup(self.envid)
        self.envdata.env_setup = True
        self.envdata.save
        
    @property
    def working_path(self):
        '''Get base path of the modeling environment identified with id.'''
        return working_path(self.envid)
    
    def compute_path(self, targetpath):
        '''Compute the real absolute path from environmental id and target path.'''
        return compute_path(self.envid, targetpath)
    
    def program_path(self, program):
        '''Return full path of a program directory (e.g. WRF, WPS ...)'''
        return program_path(self.envid, program)
    
    def set_namelist(self, program, namelist_str):
        '''
        Set namelist file for coresponding program (WRF, WPS, ARWpost).
        This function will perform necessary replacement to fit the namelist 
        into specified modeling environment
        ''' 
        if not self.verify():
            raise EnvironmentNotSetup()
        
        program_list = ['WPS', 'WRF', 'ARWpost']
        if program not in program_list:
            raise Exception('Invalid Program')
        
        from aqmrpc.wrf.namelist import decode, encode
        
        parsed_namelist = decode.decode_namelist_string(namelist_str)
        if program == 'WPS':
            filepath = os.path.join(self.program_path(program), 'namelist.wps')
            parsed_namelist['geogrid']['geog_data_path'][0] = get_geog_path()
        elif program == 'WRF':
            filepath = os.path.join(self.program_path(program), 'namelist.input')
        elif program == 'ARWpost':
            filepath = os.path.join(self.program_path(program), 'namelist.ARWpost')
            
        namelist_str_new = encode.encode_namelist(parsed_namelist)
        
        # save to file
        filepath = self.compute_path(filepath)
        
        try:
            f = open(filepath, 'wb')
        except IOError:
            return None
            
        f.write(namelist_str_new)
        f.close()
    
    def prepare_wps(self):
        '''Prepare all necessary wps data'''
        # TODO: finish this method
    
    def cleanup_wps(self):
        ''' Remove temporary files from WPS working directory '''
        if not self.verify():
            raise EnvironmentNotSetup()
        import glob
        
        wps_dir = self.program_path('WPS')
        
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
        
    def prepare_wrf(self):
        '''Symlink necessary files to run WRF'''
        if not self.verify():
            raise EnvironmentNotSetup()
        import glob
        
        wps_dir = self.program_path('WPS')
        wrf_dir = self.program_path('WRF')
        
        # symlink met_em.* files
        met_ems = glob.glob(os.path.join(wps_dir, 'met_em.*'))
        for met_em in met_ems:
            os.symlink(met_em, wrf_dir)
    
    def cleanup_wrf(self):
        '''Remove temporary files from WRF working directory '''
        if not self.verify():
            raise EnvironmentNotSetup()
        import glob
        
        wrf_dir = self.program_path('WRF')
        
        # cleanup gribfiles
        met_ems = glob.glob(os.path.join(wrf_dir, 'met_em.*'))
        for met_em in met_ems:
            os.remove(met_em)
        
        # TODO: more cleanup here...
    
    def render(self):
        '''Render model result with ARWpost'''
        pass
        

def verify_id(envid):
    '''Check if given environment id is actually valid and exist.'''
    envpath = working_path(envid) 
    try:
        os.stat(envpath)
        return True
    except OSError:
        return False

def working_path(envid):
    '''Return base path of the modeling environment identified with id.''' 
    return path.join(settings.AQM_WORKING_DIR, str(envid))

def program_path(envid, program):
    return path.join(working_path(str(envid)), program)

def compute_path(envid, targetpath):
    '''Compute the real absolute path from environmental id and target path.'''
    return path.join(working_path(str(envid)), targetpath)

def get_geog_path():
    '''Return path to geog data.'''
    return path.join(settings.AQM_MODEL_DIR, 'WRF_DATA/geog')
    
def setup(envid):
    '''
    Create a new modeling environment in AQM_WORKING_DIR location.
    Return model working path.
    '''
    base = working_path(str(envid))
    
    # recursively create symlinks to all items in AQM_MODEL_DIR
    master_path = path.join(settings.AQM_MODEL_DIR, 'WRF')
    if not path.exists(master_path):
        raise Exception('invalid AQM_MODEL_DIR setting')
    
    try:
        os.stat(base)
        # environment with specified id is already exist
        return False
    except OSError:
        pass
    
    master_tree = os.walk(master_path)
    os.mkdir(base)
    for cwd, dirs, files in master_tree:
        working_cwd = path.join(base, cwd[len(master_path)+1:])
        for dr in dirs:
            os.mkdir(path.join(working_cwd, dr))
        for f in files:
            os.symlink(path.join(cwd, f), path.join(working_cwd, f))
    
    return True

def cleanup(envid):
    '''Remove a modeling environment identified with id.'''
    try:
        shutil.rmtree(working_path(str(envid)))
    except OSError:
        pass
    
