'''
Created on Jan 27, 2012

@author: arif
'''
import unittest
import xmlrpclib


class SafeTransportWithCert(xmlrpclib.SafeTransport):
    
    def __init__(self, use_datetime=1):
        xmlrpclib.SafeTransport.__init__(self, use_datetime)
        self.__cert_file = '../../cert/cert.pem'
        self.__key_file  = '../../cert/key.pem'
        self.user_agent = 'Test Client 0.0.1'
    
    def make_connection(self,host):
        host_with_cert = (host, {
                      'key_file'  :  self.__key_file,
                      'cert_file' :  self.__cert_file
            } )
        return xmlrpclib.SafeTransport.make_connection(self, host_with_cert)


class Test(unittest.TestCase):
    '''Miscelaneous non-critical test. Server must be run with --debug=on'''
    
    def setUp(self):
        transport = SafeTransportWithCert()
        self.s = xmlrpclib.ServerProxy('https://localhost:8080', transport)
#        self.s('transport').user_agent = 'Test Client 0.0.1'
    
    def testDefer(self):
        delay = 1
        message = 'this should return same string'
        result = self.s.test.defer(delay, message)
        self.assertEqual(message, result)
        
    def testBinary(self):
        # use /bin/sh for sample binary
        # returned binary and directly read binary must have exact same length
        path = '/bin/sh'
        with open(path, 'rb') as handle:
            bin = handle.read()
        
        bin2 = self.s.test.get_binary(path).data
        self.assertEqual(len(bin), len(bin2))
    
    def testAsyncJob(self):
        '''this 4 job should be executed all at once in parallel'''
        self.s.test.async_job('test for async job!')
        self.s.test.async_job('test for async job 2!')
        self.s.test.async_job('test for async job 3!')
        self.s.test.async_job('test for async job 4!')
        self.assertEqual(1, 1)
    
    def testSubhandler(self):
        test_s = 'another test!'
        self.assertEqual(test_s, self.s.server.test_echo(test_s))
        self.assertEqual(test_s, self.s.job.test_echo(test_s))
        self.assertEqual(test_s, self.s.task.test_echo(test_s))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    