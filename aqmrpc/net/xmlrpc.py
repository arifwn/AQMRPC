'''
Created on Mar 11, 2012

@author: arif
'''

import xmlrpclib

from django.conf import settings


class SafeTransportWithCert(xmlrpclib.SafeTransport):
    
    def __init__(self, use_datetime=1):
        xmlrpclib.SafeTransport.__init__(self, use_datetime)
        self.__cert_file = settings.SSL_CERT_CERT
        self.__key_file  = settings.SSL_CERT_KEY
        self.user_agent = 'Test Client 0.0.1'
    
    def make_connection(self,host):
        host_with_cert = (host, {
                      'key_file'  :  self.__key_file,
                      'cert_file' :  self.__cert_file
            } )
        return xmlrpclib.SafeTransport.make_connection(self, host_with_cert)


class Client(xmlrpclib.ServerProxy):
    def __init__(self, uri, transport=None, encoding=None, verbose=0, allow_none=1, use_datetime=1):
        # get the url and request type
        import urllib
        reqtype, sp_uri = urllib.splittype(uri)
        
        # use custom SafeTransport to enable ssh authentication
        if transport is None:
            if reqtype == "https":
                transport = SafeTransportWithCert(use_datetime=use_datetime)
            else:
                transport = xmlrpclib.Transport(use_datetime=use_datetime)
                
        xmlrpclib.ServerProxy.__init__(self, uri, transport, encoding, verbose, allow_none, use_datetime)
        
    