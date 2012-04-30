'''
Created on Feb 24, 2012

@author: arif
'''

import os
import urllib
import shutil
from os import path

from aqmrpc import settings as aqmsettings
from aqmrpc.models import WRFEnvironment


class EnvironmentNotSetup(Exception):
    pass


class FileNotFound(Exception):
    pass


class Env(object):
    '''
    Provides access to modeling environment.
    
    Usage:
    * create / remove environment
      e = Env()
      e.setup() #creates the environment
      e.cleanup() #removes the environment
    
    * running model
      e = Env(5) #open existing environment with id=5
      #create wps namelist from namelist_string
      e.set_namelist('WPS', namelist_string) 
      e.prepare_wps() #link necessary meteorology files
      e.run_wps() #run the WPS
      e.cleanup_wps() #removes temporary files from WPS dir
    '''
    
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
        '''
        Compute the real absolute path from environmental id and target path.
        '''
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
            filepath = os.path.join(self.program_path(program),
                                    'namelist.wps')
            parsed_namelist['geogrid']['geog_data_path'][0] = get_geog_path()
        elif program == 'WRF':
            filepath = os.path.join(self.program_path(program),
                                    'namelist.input')
        elif program == 'ARWpost':
            filepath = os.path.join(self.program_path(program),
                                    'namelist.ARWpost')
            
        namelist_str_new = encode.encode_namelist(parsed_namelist)
        
        # save to file
        filepath = self.compute_path(filepath)
        
        try:
            f = open(filepath, 'wb')
        except IOError:
            return
            
        f.write(namelist_str_new)
        f.close()
    
    def get_namelist_data(self, program):
        '''Return parsed namelist data for the specified program.'''
        if not self.verify():
            raise EnvironmentNotSetup()
        
        program_list = ['WPS', 'WRF', 'ARWpost']
        if program not in program_list:
            raise Exception('Invalid Program')
        
        from aqmrpc.wrf.namelist.decode import decode_namelist
        
        if program == 'WPS':
            filepath = os.path.join(self.program_path(program),
                                    'namelist.wps')
        elif program == 'WRF':
            filepath = os.path.join(self.program_path(program),
                                    'namelist.input')
        elif program == 'ARWpost':
            filepath = os.path.join(self.program_path(program),
                                    'namelist.ARWpost')
        
        namelist_data = decode_namelist(filepath)
        return namelist_data
        
    def prepare_wps(self):
        '''
        Prepare all necessary wps data.
        
        Possible exceptions:
        * FileNotFound()
          Required files not found in cache repository
        '''
        # TODO: finish this method
        from aqmrpc.wrf.namelist.misc import parse_date_string
        
        # read the namelist to determine time periods
        namelist_data = self.get_namelist_data('WPS')
        start_date = parse_date_string(namelist_data['share']['start_date'][0])
        end_date = parse_date_string(namelist_data['share']['end_date'][0])
        
        # convert the periods into a list of file name
        fnl_list = generate_fnl_list(start_date, end_date)
        fnl_dir = os.path.join(aqmsettings.AQM_CACHE_DIR, 'fnl')
        fnl_path_list = []
        
        for filename in fnl_list:
            fnl_path = os.path.join(fnl_dir, filename)
            fnl_path_list.append(fnl_path)
            
            # check if files available in the cache directory
            try:
                os.stat(fnl_path)
                fnl_exist = True
            except OSError:
                fnl_exist = False
            
            if (not fnl_exist) and (aqmsettings.AQM_REMOTE_CACHE is not None):
                # attemp to download the file from remote cache to local cache
                network_path = '%s/fnl/%s' % (aqmsettings.AQM_REMOTE_CACHE,
                                              filename)
                try:
                    urllib.urlretrieve(network_path, fnl_path)
                except IOError:
                    raise FileNotFound(filename)
            elif not fnl_exist:
                # file not in cache directory and no remote cache configured
                # no remote cache configured
                raise FileNotFound(filename)
                
        
        # if all required files available, create symlinks to those files
        wps_path = self.program_path('WPS')
        for i, fnl_path in enumerate(fnl_path_list):
            filename = get_gribfile_name(i)
            os.symlink(fnl_path, os.path.join(wps_path, filename))
        
        # TODO: when file not found in local cache, check the remote cache 
        #       if AQM_REMOTE_CACHE set
        # if available in remote cache, copy those files to local cache
        #   and create symlinks to those files
    
    def run_wps(self):
        '''Run WPS'''
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        # run ungrib
        self.envdata.current_step = 'ungrib'
        self.envdata.running = True
        self.envdata.error = False
        self.envdata.save()
        if c.run_wps_ungrib():
            self.envdata.running = False
            self.envdata.error = False
            self.envdata.save()
        else:
            self.envdata.running = False
            self.envdata.error = True
            self.envdata.save()
            return False
        
        # run geogrid
        self.envdata.last_step = 'ungrib'
        self.envdata.current_step = 'geogrid'
        self.envdata.running = True
        self.envdata.error = False
        self.envdata.save()
        if c.run_wps_geogrid():
            self.envdata.running = False
            self.envdata.error = False
            self.envdata.save()
        else:
            self.envdata.running = False
            self.envdata.error = True
            self.envdata.save()
            return False
        
        # run metgrid
        self.envdata.last_step = 'geogrid'
        self.envdata.current_step = 'metgrid'
        self.envdata.running = True
        self.envdata.error = False
        self.envdata.save()
        if c.run_wps_metgrid():
            self.envdata.running = False
            self.envdata.error = False
            self.envdata.save()
        else:
            self.envdata.running = False
            self.envdata.error = True
            self.envdata.save()
            return False
        
        return True
    
    def stop_wps(self):
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        c.terminate_wps_ungrib()
        c.terminate_wps_geogrid()
        c.terminate_wps_metgrid()
    
    def cleanup_wps(self):
        '''Remove temporary files from WPS working directory '''
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
            filename = os.path.basename(met_em)
            os.symlink(met_em, os.path.join(wrf_dir, filename))
    
    def run_wrf(self):
        '''Run WRF'''
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        # run real
        self.envdata.current_step = 'real'
        self.envdata.running = True
        self.envdata.error = False
        self.envdata.save()
        if c.run_wrf_real():
            self.envdata.running = False
            self.envdata.error = False
            self.envdata.save()
        else:
            self.envdata.running = False
            self.envdata.error = True
            self.envdata.save()
            return False
        
        # run wrf
        self.envdata.last_step = 'real'
        self.envdata.current_step = 'wrf'
        self.envdata.running = True
        self.envdata.error = False
        self.envdata.save()
        if c.run_wrf():
            self.envdata.running = False
            self.envdata.error = False
            self.envdata.save()
        else:
            self.envdata.running = False
            self.envdata.error = True
            self.envdata.save()
            return False
        
        return True
    
    def stop_wrf(self):
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        c.terminate_wrf_real()
        c.terminate_wrf()
        
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
        
    
    def get_running_operation(self, first_check=None):
        '''Return running operation (WPS, WRF, etc...'''
        # check ungrib, geogrid, metgrid, real, wrf, arwpost to see 
        # which one is running
        # if first_check is specified, check start at that one instead of
        # ungrib
    
    def update_database(self):
        '''
        Update database model state with the real environment state.
        Used to synchronize state in the event that AQMRPC server killed
        or restarted but child job (which run outside of AQMRPC instance)
        finished successfully or still running.
        '''
    
    def resume_wps(self):
        '''
        Reconnect to running WPS runner.
        If WPS runner is not running, return the result of runner immediately.
        '''
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        if (self.envdata.current_step == 'ungrib') and \
           (self.envdata.running == True):
            # try to resume ungrib.exe
            if c.resume_wps_ungrib():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
            # continue to geogrid and metgrid
            # run geogrid
            self.envdata.last_step = 'ungrib'
            self.envdata.current_step = 'geogrid'
            self.envdata.running = True
            self.envdata.error = False
            self.envdata.save()
            if c.run_wps_geogrid():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
            # run metgrid
            self.envdata.last_step = 'geogrid'
            self.envdata.current_step = 'metgrid'
            self.envdata.running = True
            self.envdata.error = False
            self.envdata.save()
            if c.run_wps_metgrid():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
        elif (self.envdata.current_step == 'geogrid') and \
           (self.envdata.running == True):
            # try to resume geogrid.exe
            if c.resume_wps_geogrid():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
            # continue to metgrid
            
            # run metgrid
            self.envdata.last_step = 'geogrid'
            self.envdata.current_step = 'metgrid'
            self.envdata.running = True
            self.envdata.error = False
            self.envdata.save()
            if c.run_wps_metgrid():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
        elif (self.envdata.current_step == 'metgrid') and \
           (self.envdata.running == True):
            # try to resume metgrid.exe
            if c.resume_wps_metgrid():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
        
        return True
    
    def resume_wrf(self):
        '''
        Reconnect to running WRF runner.
        If WRF runner is not running, return the result of runner immediately.
        '''
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        if (self.envdata.current_step == 'real') and \
           (self.envdata.running == True):
            # try to resume real.exe
            if c.resume_wrf_real():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
            # continue to WRF
            self.envdata.last_step = 'real'
            self.envdata.current_step = 'wrf'
            self.envdata.running = True
            self.envdata.error = False
            self.envdata.save()
            if c.run_wrf():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
            
        elif (self.envdata.current_step == 'wrf') and \
           (self.envdata.running == True):
            # try to resume wrf
            if c.resume_wrf():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
        
        return True
    
    def set_arwpost_namelist(self, namelist_str, wrfout_path, grads_basename,
                             start_date=None, end_date=None):
        '''set ARWpost namelist with specified parameters'''
        
        if not self.verify():
            raise EnvironmentNotSetup()
        
        from aqmrpc.wrf.namelist import decode, encode
        
        parsed_namelist = decode.decode_namelist_string(namelist_str)
        parsed_namelist['io']['input_root_name'][0] = wrfout_path
        parsed_namelist['io']['output_root_name'][0] = grads_basename
        
        if start_date is not None:
            parsed_namelist['datetime']['start_date'][0] = start_date
        if end_date is not None:
            parsed_namelist['datetime']['end_date'][0] = end_date
        
        namelist_str_new = encode.encode_namelist(parsed_namelist)
        
        # save to file
        filepath = os.path.join(self.program_path('ARWpost'),
                                'namelist.ARWpost')
        filepath = self.compute_path(filepath)
        
        try:
            f = open(filepath, 'wb')
        except IOError:
            return
            
        f.write(namelist_str_new)
        f.close()
    
    def run_arwpost(self, namelist_str):
        '''Run ARWpost and produce GrADS files'''
        # get the number of domains
        # for each domain:
        #   set input_root_name in namelist.ARWpost to appropriate wrfout file
        #   set output_root_name to appropriate domain name
        #   set start_date and end_date according to corresponding date
        #       setting in namelist.wps file (notice the domain number)
        #   run arwpost
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        wps_namelist_data = self.get_namelist_data('WPS')
        wrf_namelist_data = self.get_namelist_data('WRF')
        
        n_domain = wrf_namelist_data['domains']['max_dom'][0]
        
        for d in range(n_domain):
            domain = d + 1
            
            # get date
            start_date = wps_namelist_data['share']['start_date'][d]
            end_date = wps_namelist_data['share']['end_date'][d]
            
            # get wrfout path
            wrfout_filename = 'wrfout_d%02i_%s' % (domain, start_date)
            wrfout_path = os.path.join(self.program_path('WRF'),
                                       wrfout_filename)
            
            # is it really exist?
            os.stat(wrfout_path)
            
            # construct GrADS basename
            grads_basename = 'd%02i_%s' % (domain, start_date)
            
            # save namelist file
            self.set_arwpost_namelist(namelist_str, wrfout_path,
                                      grads_basename, start_date,
                                      end_date)
            
            # run ARWpost
            self.envdata.current_step = 'arwpost'
            self.envdata.running = True
            self.envdata.error = False
            self.envdata.save()
            if c.run_arwpost():
                self.envdata.running = False
                self.envdata.error = False
                self.envdata.save()
            else:
                self.envdata.running = False
                self.envdata.error = True
                self.envdata.save()
                return False
        
        return True
        
    def stop_arwpost(self):
        from aqmrpc.wrf.controller import ModelEnvController
        c = ModelEnvController(self.envid)
        
        c.terminate_arwpost()
    
    def render_grads(self, gs_template):
        '''Generate GrADS files from model result with ARWpost'''
        from aqmrpc.grads import controller as grads_controller
        
        ctl_files = []
        wps_namelist_data = self.get_namelist_data('WPS')
        wrf_namelist_data = self.get_namelist_data('WRF')
        n_domain = wrf_namelist_data['domains']['max_dom'][0]
        
        for d in range(n_domain):
            domain = d + 1
            
            # get date
            start_date = wps_namelist_data['share']['start_date'][d]
            
            # construct GrADS ctl filename
            ctl_file = os.path.join(self.program_path('ARWpost'),
                                    'd%02i_%s.ctl' % (domain, start_date))
            ctl_files.append(ctl_file)
        
        c = grads_controller.GradsController(self.program_path('ARWpost'),
                                             gs_template)
        c.plot(ctl_files)
        
        
        

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
    return path.join(aqmsettings.AQM_WORKING_DIR, 'WRF', str(envid))

def program_path(envid, program):
    return path.join(working_path(str(envid)), program)

def compute_path(envid, targetpath):
    '''Compute the real absolute path from environmental id and target path.'''
    return path.join(working_path(str(envid)), targetpath)

def get_geog_path():
    '''Return path to geog data.'''
    return path.join(aqmsettings.AQM_MODEL_DIR, 'WRF_DATA/geog')
    
def setup(envid):
    '''
    Create a new modeling environment in AQM_WORKING_DIR location.
    Return model working path.
    '''
    base = working_path(str(envid))
    
    # recursively create symlinks to all items in AQM_MODEL_DIR
    master_path = path.join(aqmsettings.AQM_MODEL_DIR, 'WRF')
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

def generate_fnl_list(start, end):
    '''Return a list of fnl filename from given datetime objects'''
    import datetime
    oneday = datetime.timedelta(1)
    end = end + oneday # round up the end time by one day
    
    start = datetime.datetime(start.year, start.month, start.day)
    end = datetime.datetime(end.year, end.month, end.day)
    dt = end - start
    n_files = int((dt.total_seconds() / (6 * 60 * 60)) + 1)
    
    template = 'fnl_{:04d}{:02d}{:02d}_{:02d}_00_c'
    
    filenames = []
    
    for i in xrange(n_files):
        filedate = start + datetime.timedelta(0, (i * (6 * 60 * 60)))
        filename = template.format(filedate.year, filedate.month,
                                   filedate.day, filedate.hour)
        filenames.append(filename)
    
    return filenames

def get_gribfile_name(i):
    '''Return GRIBFILE.AAA for i=0, GRIBFILE.AAB for i=1 and so on...'''
    alpha = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
             'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z')
    n = len(alpha)
    i3 = alpha[i % n]
    i2 = alpha[(i / n) % n]
    i1 = alpha[i / (n ** 2)]
    
    name = 'GRIBFILE.%s%s%s' % (i1, i2, i3)
    return name
