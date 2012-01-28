'''
Created on Jan 27, 2012

@author: arif
'''
import unittest
import xmlrpclib


class Test(unittest.TestCase):

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
        
        bin2 = self.s.test_get_binary(path).data
        self.assertEqual(len(bin), len(bin2))
    
    def testAsyncJob(self):
        self.s.test_async_job('test for async job!')
        self.s.test_async_job('test for async job 2!')
        self.s.test_async_job('test for async job 3!')
        self.s.test_async_job('test for async job 4!')
        self.assertEqual(1, 1)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    