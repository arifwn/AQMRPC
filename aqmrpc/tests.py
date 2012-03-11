'''
Created on Jan 22, 2012

@author: arif
'''

import unittest

from aqmrpc.net.xmlrpc import Client


class WRFEnvTest(unittest.TestCase):
    
    def setUp(self):
        self.client = Client('https://localhost:8080')
    
    def testCreateEnv(self):
        self.assertIsNotNone(self.client.wrf.setupenv())
    
    def testCleanupEnv(self):
        self.assertIsNotNone(self.client.wrf.cleanupenv('1'), True)