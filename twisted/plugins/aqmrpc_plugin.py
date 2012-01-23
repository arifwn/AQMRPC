'''
AQM RPC Server

foreground: twistd -n aqmrpc
background (demonized): twistd aqmrpc

Created on Jan 22, 2012

@author: arif
'''
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service
from twisted.web import server, resource, xmlrpc

from aqmrpc import interface

if hasattr(settings, 'RPCSERVER_DEFAULT_ADDR'):
    DEFAULT_ADDR = settings.RPCSERVER_DEFAULT_ADDR
else:
    DEFAULT_ADDR = ''
    
if hasattr(settings, 'RPCSERVER_DEFAULT_PORT'):
    DEFAULT_PORT = int(settings.RPCSERVER_DEFAULT_PORT)
else:
    DEFAULT_PORT = 8080

class Options(usage.Options):
    optParameters = [["port", "p", DEFAULT_PORT, "The port number to listen on."],
                     ["address", "a", DEFAULT_ADDR, "The address to listen on."]]

class AQMServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqmrpc"
    description = "AQM RPC Server"
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer that contains RPC Server.
        """
        root = resource.Resource()
        r = interface.Interface()
        xmlrpc.addIntrospection(r)
        root.putChild('RPC2', r)
        
        main_site = server.Site(root)
        return internet.TCPServer(int(options["port"]), main_site, interface=options['address'])

serviceMaker = AQMServiceMaker()
