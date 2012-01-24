'''
Created on Sep 28, 2011

@author: Arif
'''

import time
from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer


def block_2s(data):
    ''' this function block for 5 seconds before returning any data.
    '''
    time.sleep(2)
    return data

def test_defer_to_thread(data):
    ''' while block_5s() blocks for 5 seconds, deferToThread makes sure that
    Twisted event loop do not get blocked'''
    d = threads.deferToThread(block_2s, data)
    return d


class Interface(xmlrpc.XMLRPC):
    
    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        
    def xmlrpc_test_thread(self):
        pass
    
    def xmlrpc_test_defer(self):
        d = test_defer_to_thread('Hello, sorry it took so long :)')
        return d
    