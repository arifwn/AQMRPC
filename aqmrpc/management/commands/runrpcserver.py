from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import twisted.web
import twisted.internet

from aqmrpc import interface


class Command(BaseCommand):
    help = "Starts the RPC Server."

    if hasattr(settings, 'RPCSERVER_DEFAULT_PORT'):
        DEFAULT_PORT = str(settings.RPCSERVER_DEFAULT_PORT)
    else:
        DEFAULT_PORT = 8080

    def handle(self, addrport='', *args, **options):
        print 'Starting RPC Server on port %d' % self.DEFAULT_PORT
        print 'Quit the server with CONTROL-C.'
        
        root = twisted.web.resource.Resource()
        r = interface.Interface()
        twisted.web.xmlrpc.addIntrospection(r)
        root.putChild('RPC2', r)
        twisted.internet.reactor.listenTCP(self.DEFAULT_PORT, twisted.web.server.Site(root))
        twisted.internet.reactor.run()
        