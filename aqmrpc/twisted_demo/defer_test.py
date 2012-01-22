'''
Created on Jan 22, 2012

@author: arif
'''
import time
from twisted.internet import threads, reactor

def block_5s(data):
    ''' this function block for 5 seconds before returning any data.
    '''
    time.sleep(5)
    return data

def test_defer_to_thread(data):
    ''' while block_5s() blocks for 5 seconds, deferToThread makes sure that
    Twisted event loop do not get blocked'''
    d = threads.deferToThread(block_5s, data)
    return d
