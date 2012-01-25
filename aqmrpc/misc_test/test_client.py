'''
Created on Sep 28, 2011

@author: Arif
'''
from django.utils import unittest
import xmlrpclib

class RPCTestInterface(unittest.TestCase):
    
    def setUp(self):
        self.s = xmlrpclib.ServerProxy('http://localhost:8080')
        self.s('transport').user_agent = 'Test Client 0.0.1'
    
    def testDefer(self):
        delay = 1
        message = 'this should return same string'
        result = self.s.test_defer(delay, message)
        self.assertEqual(message, result)
        
    def testBinary(self):
        # use /bin/sh for sample binary
        # returned binary and directly read binary must have exact same length
        path = '/bin/sh'
        with open(path, 'rb') as handle:
            bin = handle.read()
        
        bin2 = self.s.get_binary(path).data
        self.assertEqual(len(bin), len(bin2))
        