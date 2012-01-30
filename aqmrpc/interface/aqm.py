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
    
    def __init__(self, allowNone=False, useDateTime=True):
        xmlrpc.XMLRPC.__init__(self, allowNone, useDateTime)
        
        self.server_handler = Server()
        self.putSubHandler('server', self.server_handler)
        
        self.server_handler = Job()
        self.putSubHandler('job', self.server_handler)
        
        self.server_handler = Task()
        self.putSubHandler('task', self.server_handler)


class Server(xmlrpc.XMLRPC):
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_test_echo(self, s):
        return s
    

class Job(xmlrpc.XMLRPC):
    
    def xmlrpc_create(self, config):
        return 'id'
    
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_test_echo(self, s):
        return s
    

class Task(xmlrpc.XMLRPC):
    
    def xmlrpc_create(self, config):
        return 'id'
        
    def xmlrpc_all(self):
        return []
    
    def xmlrpc_filter(self, **kwargs):
        return []
    
    def xmlrpc_status(self, id):
        return []
    
    def xmlrpc_info(self, id):
        return []
    
    def xmlrpc_archive(self, id):
        return True
    
    def xmlrpc_remove(self, id):
        return True
    
    def xmlrpc_result(self, id):
        return {'result': True}
    
    def xmlrpc_test_echo(self, s):
        return s
    
