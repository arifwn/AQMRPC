'''
Created on Jan 22, 2012

@author: arif
'''

import os
import unittest

from aqmrpc.net.xmlrpc import Client


class WRFEnvTest(unittest.TestCase):
    '''Run RPC Server before running this test'''
    
    def setUp(self):
        # WARNING: this test use envid = 1
        self.envid = 1
        
        self.client = Client('https://localhost:8080')
        envid = self.client.wrf.setupenv(self.envid)
        if envid is None:
            envid = self.client.wrf.setupenv()
            self.assertEqual(envid, self.envid, 'Failed to create modeling environment!')
    
    def tearDown(self):
        self.assertTrue(self.client.wrf.cleanupenv(self.envid))

    
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
        
        with open(os.path.join(os.path.dirname(misc.__file__),'test/namelist.input'), 'rb') as f:
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
    
    