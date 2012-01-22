'''
Created on Sep 28, 2011

@author: Arif
'''
import sys
import os
import time
import atexit
import SocketServer
from signal import SIGTERM 
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer): 
    pass

if __name__ == '__main__':
    import interface
    
    print 'Running RPC Server...'
    address = ('localhost', 8080)
    
    # Create server
    server = AsyncXMLRPCServer(address, requestHandler=SimpleXMLRPCRequestHandler)
    server.register_introspection_functions()
    
    # Register instance containing methods to be exposed
    server.register_instance(interface.Interface())
    
    # Run the server
    server.serve_forever()
    