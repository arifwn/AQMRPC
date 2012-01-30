'''
Created on Jan 26, 2012

@author: arif
'''
import time
import xmlrpclib

from twisted.web import xmlrpc
from twisted.internet import threads, reactor, defer
from twisted.python import threadpool


class Interface(xmlrpc.XMLRPC):
    
    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        
        self.server_handler = Server()
        self.putSubHandler('server', self.server_handler)
        
        self.server_handler = Job()
        self.putSubHandler('job', self.server_handler)
        
        self.server_handler = Task()
        self.putSubHandler('task', self.server_handler)


class Server(xmlrpc.XMLRPC):
    
    def xmlrpc_test_echo(self, s):
        return s
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    

class Job(xmlrpc.XMLRPC):
    
    def xmlrpc_test_echo(self, s):
        return s
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    

class Task(xmlrpc.XMLRPC):
    
    def xmlrpc_test_echo(self, s):
        return s
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
