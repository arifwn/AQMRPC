'''
Created on Jan 24, 2012

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

from aqmrpc.interface import test as aqmtest
from aqmrpc.interface import aqm
from servercon import supervisor


DEBUG = getattr(settings, 'DEBUG', True)
DEFAULT_ADDR = getattr(settings, 'RPCSERVER_DEFAULT_ADDR', '')
DEFAULT_PORT = int(getattr(settings, 'RPCSERVER_DEFAULT_PORT', 8080))


class Options(usage.Options):
    optParameters = [["port", "p", DEFAULT_PORT, "The port number to listen on."],
                     ["address", "a", DEFAULT_ADDR, "The address to listen on."]]


class AQMServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqmrpc"
    description = "AQM RPC Server"
    options = Options

    def makeService(self, options):
        """Construct a TCPServer which contains AQM RPC Server."""
        
        # make a new MultiService to hold the thread/web services
        multi = service.MultiService()
        
        # make a new SupervisorService and add it to the multi service
        sv = supervisor.SupervisorService()
        sv.setServiceParent(multi)
        
        root = resource.Resource()
        
        if DEBUG:
            r = aqmtest.Interface()
        else:
            r = aqm.Interface()
            
        xmlrpc.addIntrospection(r)
        root.putChild('RPC2', r)
        
        main_site = server.Site(root)
        ws = internet.TCPServer(int(options["port"]), main_site, 
                                interface=options['address'])
        
        # add the web server service to the multi service
        ws.setServiceParent(multi)
        return multi
        
