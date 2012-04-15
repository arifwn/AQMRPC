from django.conf import settings
import rest.client
import aqmrpc

class AQMConnection(rest.client.Connection):
    
    def __init__(self):
        super(AQMConnection, self).__init__(settings.AQMWEB_URL,
                                   username=settings.AQMWEB_CREDENTIAL[0],
                                   password=settings.AQMWEB_CREDENTIAL[1],
                                   ca_certs=settings.SSL_CERT_CACERT,
                                   user_agent_name='AQM RPC Server %s' % aqmrpc.__version__)
