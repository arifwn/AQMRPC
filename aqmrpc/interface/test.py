'''
Created on Sep 28, 2011

@author: Arif
'''

import time
from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool
import xmlrpclib


class Interface(xmlrpc.XMLRPC):
    
    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        self.pool = threadpool.ThreadPool()
    
    
    def block_2s(self, data):
        ''' this function block for 5 seconds before returning any data.
        '''
        time.sleep(2)
        return data
    
    def xmlrpc_test_defer(self):
        ''' while block_5s() blocks for 5 seconds, deferToThread makes sure that
        Twisted event loop do not get blocked'''
        d = threads.deferToThread(self.block_2s, 'Hello, sorry it took so long :)')
        return d
    
    
    def return_binary(self, path):
        ''' return binary data from specified path
        '''
        with open(path, 'rb') as handle:
                return xmlrpclib.Binary(handle.read())
            
    def xmlrpc_test_binary(self):
        '''return binary data, use deferToThread so it doesn't block'''
        d = threads.deferToThread(self.return_binary, 'urls.py')
        return d
        