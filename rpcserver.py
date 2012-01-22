'''
Run RPC Server with twistd command:
foreground: twistd -ny rpcserver.py
background (demonized): twistd -y rpcserver.py

Created on Jan 22, 2012

@author: arif
'''
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from twisted.application import internet, service
from twisted.web import server, resource, xmlrpc
import twisted.internet

from aqmrpc import interface

from django.conf import settings

if hasattr(settings, 'RPCSERVER_DEFAULT_PORT'):
    PORT = str(settings.RPCSERVER_DEFAULT_PORT)
else:
    PORT = 8080

# Twisted Application Framework setup:
application = service.Application('aqmrpc')

root = resource.Resource()
r = interface.Interface()
xmlrpc.addIntrospection(r)
root.putChild('RPC2', r)

# Serve it up:
main_site = server.Site(root)
internet.TCPServer(PORT, main_site).setServiceParent(application)
