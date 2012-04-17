
import json
import urllib

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


def command(command, data=None):
    ''' Send command to machine-to-machine rest handler. '''
    body = {}
    body_encoded = None
    if data is not None:
        data_json = json.dumps(data)
        body['data'] = data_json
    
    body['command'] = command
    body['server_id'] = settings.AQM_SERVER_ID
    body_encoded = urllib.urlencode(body)
    
    c = AQMConnection()
    response = c.request_post('rest/m2m', body=body_encoded)
    return response
