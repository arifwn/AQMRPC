'''
Created on Feb 24, 2012

@author: arif
'''

import os.path

from django.conf import settings


AQM_MODEL_DIR = getattr(settings, 'AQM_MODEL_DIR', '/home/arif/AQMDir/master')
AQM_WORKING_DIR = getattr(settings, 'AQM_WORKING_DIR', '/home/arif/AQMDir/working')
AQM_PYTHON_BIN = getattr(settings, 'AQM_PYTHON_BIN', '/usr/bin/python')

AQM_CERT_CERT = getattr(settings, 'AQM_CERT_CERT', './cert/cert.pem')
AQM_CERT_KEY = getattr(settings, 'AQM_CERT_KEY', './cert/key.pem')
AQM_CERT_CACERT = getattr(settings, 'AQM_CERT_CACERT', './cert/cacert.pem')

AQM_CACHE_DIR = getattr(settings, 'AQM_CACHE_DIR', os.path.join(AQM_MODEL_DIR, 'WRF_DATA/cache'))

# can be http or ftp, should be none if no remote cache configured
AQM_REMOTE_CACHE = getattr(settings, 'AQM_REMOTE_CACHE', 'ftp://localhost/upload/cache/')

# GrADS
GRADS_BIN = getattr(settings, 'GRADS_BIN', '/usr/local/bin/grads')

