
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
    response = c.request_post('rest/m2m/', body=body_encoded)
    
    if response['headers']['status'] == '200':
        if response['headers']['content-type'] == 'application/json; charset=utf-8':
            
            return json.loads(response['body'])
        else:
            return response['body']
    else:
        raise IOError(response['headers']['status'])

def command_confirm_run(task_id):
    return command('confirm_run', {'task_id': task_id})
    
def command_report_run_stage(task_id, envid, stage):
    return command('report_run_stage', {'task_id': task_id, 'envid': envid, 'stage': stage})
    
def command_job_finished(task_id):
    return command('job_finished', {'task_id': task_id})
    