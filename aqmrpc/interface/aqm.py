'''
Created on Jan 26, 2012

@author: arif
'''
import time
from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool
import xmlrpclib

class Interface(xmlrpc.XMLRPC):
    pass