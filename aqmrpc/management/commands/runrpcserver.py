from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
import os
import sys
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from aqmrpc.server import AsyncXMLRPCServer
from aqmrpc import pidencrypt
from aqmrpc import interface

class Command(BaseCommand):
    help = "Starts the RPC Server."

    if hasattr(settings, 'RPCSERVER_DEFAULT_ADDR'):
        DEFAULT_ADDR = settings.RPCSERVER_DEFAULT_ADDR
    else:
        DEFAULT_ADDR = '127.0.0.1'
    if hasattr(settings, 'RPCSERVER_DEFAULT_PORT'):
        DEFAULT_PORT = str(settings.RPCSERVER_DEFAULT_PORT)
    else:
        DEFAULT_PORT = 8080
    

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        print 'Starting RPC Server on %s:%s' % (self.DEFAULT_ADDR, self.DEFAULT_PORT)
        print 'Quit the server with CONTROL-C.'
        
        # Create server
        server = AsyncXMLRPCServer((self.DEFAULT_ADDR, self.DEFAULT_PORT), requestHandler=SimpleXMLRPCRequestHandler)
        server.register_introspection_functions()
        
        # Register instance containing methods to be exposed
        server.register_instance(interface.Interface())
    
        # Run the server
        server.serve_forever()
        