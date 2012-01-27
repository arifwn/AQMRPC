'''
Created on Sep 28, 2011

@author: Arif
'''

import time
import xmlrpclib

from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool

from aqmrpc.interface import aqm
from aqmrpc.jobs.test import TestJob
from servercon import supervisor


class Interface(aqm.Interface):
    
    def __init__(self):
        aqm.Interface.__init__(self)
        self.pool = threadpool.ThreadPool()
    
    def t_block_and_return(self, delay, data):
        ''' this function block for 'delay' seconds before returning any data.
        '''
        time.sleep(delay)
        return data
    
    def xmlrpc_test_defer(self, delay, message):
        ''' while block_5s() blocks for 5 seconds, deferToThread makes sure that
        Twisted event loop do not get blocked'''
        d = threads.deferToThread(self.t_block_and_return, delay, message)
        return d
    
    def t_return_binary(self, path):
        ''' return binary data from specified path
        '''
        with open(path, 'rb') as handle:
                return xmlrpclib.Binary(handle.read())
            
    def xmlrpc_test_get_binary(self, path):
        '''return binary data, use deferToThread so it doesn't block'''
        d = threads.deferToThread(self.t_return_binary, path)
        return d
    
    def xmlrpc_test_async_job(self, data):
        j = TestJob(str(data))
        supervisor.put_job(j)
        return True
    