'''
Created on Jan 22, 2012

@author: arif
'''

import os
import unittest


class RPCBehaviorTest(unittest.TestCase):
    '''
    Test behavior of the RPC Server.
    Run RPC Server before running this test.
    '''
    
    def setUp(self):
        from aqmrpc.net.xmlrpc import Client
        
        # WARNING: this test use envid = 1
        self.envid = 1
        
        self.client = Client('https://localhost:8080')
        
        # check if rpc server is up and running
        
        test_str = 'The rabbit has escaped!'
        self.client.server.test_echo(test_str)
        
        envid = self.client.wrf.setupenv(self.envid)
        if envid is None:
            envid = self.client.wrf.setupenv()
            self.assertEqual(envid, self.envid, 'Failed to create modeling environment!')
    
    #def tearDown(self):
    #    self.assertTrue(self.client.wrf.cleanupenv(self.envid))

    
    def testFilesystem(self):
        '''Test Filesystem API'''
        
        data = 'this is just a test yo!'
        filename = 'unit-test-temp.txt'
        self.client.filesystem.write(self.envid, filename, data)
        self.assertTrue(self.client.filesystem.exist(self.envid, filename), 
                        'filesystem write failed!')
        
        read_data = self.client.filesystem.read(self.envid, filename).data
        self.assertEqual(data, read_data, 'filesystem read failed')
        
        self.client.filesystem.remove(self.envid, filename)
        
    def testWPSNamelist(self):
        '''Test creation of WPS Namelist file'''
        from aqmrpc.wrf import environment as wrfenv
        from aqmrpc.wrf.namelist import decode, encode
        
        with open(os.path.join(os.path.dirname(decode.__file__),'test/namelist.wps'), 'rb') as f:
            namelist_str = f.read()
        
        self.client.wrf.set_namelist(self.envid, 'WPS', namelist_str)
        with open(os.path.join(wrfenv.program_path(self.envid, 'WPS'), 'namelist.wps'), 'rb') as f:
            namelist_new_str = f.read()
        
        parsed_namelist = decode.decode_namelist_string(namelist_str)
        parsed_namelist['geogrid']['geog_data_path'][0] = wrfenv.get_geog_path()
        
        self.assertEqual(namelist_new_str, encode.encode_namelist(parsed_namelist))
    
    def testWRFNamelist(self):
        '''Test creation of WRF Namelist file'''
        from aqmrpc.wrf import environment as wrfenv
        from aqmrpc.wrf.namelist import misc
        
        with open(os.path.join(os.path.dirname(misc.__file__), 'test/namelist.input'), 'rb') as f:
            namelist_str = f.read()
        
        self.client.wrf.set_namelist(self.envid, 'WRF', namelist_str)
        with open(os.path.join(wrfenv.program_path(self.envid, 'WRF'), 'namelist.input'), 'rb') as f:
            namelist_new_str = f.read()
        self.assertEqual(namelist_new_str, namelist_str)
    
    def testARWpostNamelist(self):
        '''Test creation of ARWpost Namelist file'''
        from aqmrpc.wrf import environment as wrfenv
        from aqmrpc.wrf.namelist import misc
        
        with open(os.path.join(os.path.dirname(misc.__file__),'test/namelist.ARWpost'), 'rb') as f:
            namelist_str = f.read()
        
        self.client.wrf.set_namelist(self.envid, 'ARWpost', namelist_str)
        with open(os.path.join(wrfenv.program_path(self.envid, 'ARWpost'), 'namelist.ARWpost'), 'rb') as f:
            namelist_new_str = f.read()
        self.assertEqual(namelist_new_str, namelist_str)
    
    def testWRFjob(self):
        from aqmrpc.wrf import environment as wrfenv
        from aqmrpc.grads import controller as grcon
        sample_gs_template = os.path.join(os.path.dirname(grcon.__file__), 'test/plot_all.gs')
        wps_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.wps')
        wrf_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.input')
        arwpost_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.ARWpost')
        
        data = {}
        data['name'] = 'test_job'
        data['id'] = 1
        with open(wrf_namelist, 'r') as f:
            data['WRFnamelist'] = f.read()
        with open(wps_namelist, 'r') as f:
            data['WPSnamelist'] = f.read()
        with open(arwpost_namelist, 'r') as f:
            data['ARWpostnamelist'] = f.read()
        with open(sample_gs_template, 'r') as f:
            data['grads_template'] = f.read()
        
        self.client.wrf.add_job(data, 1)
    
    def testWRFstopjob(self):
        self.client.wrf.stop_job(1)
    
    
    def testGetPlot(self):
        res = self.client.wrf.get_plot(5, 1)
        print res, len(res)
    

class WRFEnvTest(unittest.TestCase):
    '''
    Unit Test for wrf.environment module.
    '''
    
    def setUp(self):
        from aqmrpc.wrf import environment as wrfenv
        
        self.wps_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.wps')
        self.wrf_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.input')
        self.arwpost_namelist = os.path.join(os.path.dirname(wrfenv.__file__), 'namelist/test/namelist.ARWpost')
        
        self.env = wrfenv.Env(1)
        
        #creates the environment
        self.env.setup()
        
    
    def tearDown(self):
        #removes the environment
        self.env.cleanup()
    
    def check_wps_result(self, subprogram):
        '''check whether ungrib run successfully'''
        program_list = ['ungrib', 'geogrid', 'metgrid']
        if subprogram not in program_list:
            raise Exception('invalid subprogram: %s' % subprogram)
        
        log_path = os.path.join(self.env.program_path('WPS'), '%s.log' % subprogram)
        
        tag = '*** Successful completion of program %s.exe ***' % subprogram
        with open(log_path, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def check_wrf_result(self, subprogram):
        '''check whether ungrib run successfully'''
        program_list = ['real', 'wrf']
        if subprogram not in program_list:
            raise Exception('invalid subprogram: %s' % subprogram)
        
        log_path = os.path.join(self.env.program_path('WRF'), '%s_stdout.txt' % subprogram)
        
        if subprogram == 'real':
            tag = 'SUCCESS COMPLETE REAL_EM INIT'
        else:
            tag = 'SUCCESS COMPLETE WRF'
        with open(log_path, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag:
                return True
        return False
    
    def check_arwpost_result(self):
        '''check whether arwpost run successfully'''
        
        log_path = os.path.join(self.env.program_path('ARWpost'), 'arwpost_stdout.txt')
        tag = '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!  Successful completion of ARWpost  !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
        with open(log_path, 'r') as f:
            f.seek(-(len(tag)+1), os.SEEK_END)
            data = f.read().strip()
            if data == tag.strip():
                return True
        return False
    
    
    def testWRF(self):
        '''Test WRF Runner.'''
        
        # Run WPS
        
        # Get sample namelist.wps
        with open(self.wps_namelist, 'r') as f:
            namelist = f.read()
        
        self.env.set_namelist('WPS', namelist)
        
        self.env.prepare_wps()
        self.env.run_wps()
        self.env.cleanup_wps()
        
        # check whether the operation finished successfully
        self.assertTrue(self.check_wps_result('ungrib'))
        self.assertTrue(self.check_wps_result('geogrid'))
        self.assertTrue(self.check_wps_result('metgrid'))
        
        # Run WRF
        with open(self.wrf_namelist, 'r') as f:
            namelist = f.read()
        
        self.env.set_namelist('WRF', namelist)
        self.env.prepare_wrf()
        self.env.run_wrf()
        self.env.cleanup_wrf()
        
        self.assertTrue(self.check_wrf_result('real'))
        self.assertTrue(self.check_wrf_result('wrf'))
    
        # Run ARWpost
        import glob
        
        # Get sample namelist.ARWpost
        with open(self.arwpost_namelist, 'r') as f:
            namelist_str = f.read()
        
        self.assertTrue(self.env.run_arwpost(namelist_str))
        self.assertTrue(self.check_arwpost_result())
        
        # Render result with GrADS
        from aqmrpc.grads import controller as grcon
        sample_gs_template = os.path.join(os.path.dirname(grcon.__file__), 'test/plot_all.gs')
        with open(sample_gs_template, 'r') as f:
            gs_tmp = f.read()
        self.env.render_grads(gs_tmp)
    
   
class UtilitiesTest(unittest.TestCase):
    ''' Test various utility in aqmrpc system '''
    
    def testRestAPI(self):
        import json
        from aqmrpc.misc.rest_client import AQMConnection
        
        c = AQMConnection()
        response = c.request_get('rest/chemdata/detail/1/')
        data = json.loads(response['body'])
        print response['body']
        
        self.assertEqual(data['name'], u'Test Emission Data')
    
    def testConfirmJob(self):
        from aqmrpc.misc.rest_client import command_confirm_run
        
        ret = command_confirm_run(1)
        self.assertEqual(ret, True)
    
    