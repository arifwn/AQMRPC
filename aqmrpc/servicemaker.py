'''
Created on Jan 24, 2012

@author: arif
'''
import os
import xmlrpclib

from OpenSSL import SSL

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service
from twisted.web import server, resource, xmlrpc
from twisted.internet import ssl
from twisted.python import log

from aqmrpc.interface import test as aqmtest
from aqmrpc.interface import aqm
from aqmrpc import settings as aqmsettings
from servercon import supervisor


if(getattr(settings, 'DEBUG', True)):
    DEBUG = 'on'
else:
    DEBUG = 'off'

DEFAULT_ADDR = getattr(settings, 'RPCSERVER_DEFAULT_ADDR', '')
DEFAULT_PORT = getattr(settings, 'RPCSERVER_DEFAULT_PORT', '8080')


class Options(usage.Options):
    optParameters = [['port', 'p', DEFAULT_PORT, "The port number to listen on."],
                     ['address', 'a', DEFAULT_ADDR, "The address to listen on."],
                     ['debug', 'd', DEBUG, "'on': enable debug mode"]]


class SiteFactory(server.Site):
    '''Customized logging format'''
    
    def log(self, request):
        """
        Log a request's result to the logfile, by default in combined log format.
        """
        if hasattr(self, "logFile"):
            line = '%s - - %s "%s" %d %s "%s" "%s"\n' % (
                request.getClientIP(),
                # request.getUser() or "-", # the remote user is almost never important
                self._logDateTime,
                '%s %s %s' % (self._escape(request.method),
                              self._escape(request.uri),
                              self._escape(request.clientproto),),
                request.code,
                request.sentLength or "-",
                self._escape(request.getHeader("referer") or "-"),
                self._escape(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)


def verifyCallback(connection, x509, errnum, errdepth, ok):
    if not ok:
        log.msg('invalid cert from subject: %s' % x509.get_subject())
        return False
    else:
        return True

#def startup_processing():
#    '''Performs early checks before starting the server'''
#    from aqmrpc.models import WRFEnvironment
#    
#    # id number 1 is used for testing purpose. Make sure it already exist
#    try:
#        envdata = WRFEnvironment.objects.get(id=1)
#    except WRFEnvironment.DoesNotExist:
#        envdata = WRFEnvironment(id=1)
#        envdata.save()


class AQMServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqmrpc"
    description = "AQM RPC Server"
    options = Options

    def makeService(self, options):
        """Construct a TCPServer which contains AQM RPC Server."""
        
        # make a new MultiService to hold the thread/web services
        multi = service.MultiService()
        
        # performs some startup preparation
#        startup_processing()
        
        # make a new SupervisorService and add it to the multi service
        sv = supervisor.SupervisorService()
        sv.setServiceParent(multi)
        
        root = resource.Resource()
        r = aqm.Interface()
        
        if DEBUG == 'on':
            # Starting server with --debug=on
            r.putSubHandler('test', aqmtest.TestInterface())
        
        # setup ssl context
        myContextFactory = ssl.DefaultOpenSSLContextFactory(aqmsettings.AQM_CERT_KEY,
                                                            aqmsettings.AQM_CERT_CERT)
        ctx = myContextFactory.getContext()
        ctx.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
                       verifyCallback)
        
        # Since we have self-signed certs we have to explicitly
        # tell the server to trust them.
        ctx.load_verify_locations(aqmsettings.AQM_CERT_CACERT)
        
        xmlrpc.addIntrospection(r)
        root.putChild('RPC2', r)
        
        main_site = SiteFactory(root)
        ws = internet.SSLServer(int(options["port"]), main_site,
                                myContextFactory,
                                interface=options['address'])
#        ws = internet.TCPServer(int(options["port"]), main_site, 
#                                interface=options['address'])
        
        # add the web server service to the multi service
        ws.setServiceParent(multi)
        return multi
        
