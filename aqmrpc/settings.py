'''
Created on Feb 24, 2012

@author: arif
'''

import os

from django.conf import settings


AQM_MODEL_DIR = getattr(settings, 'AQM_MODEL_DIR', '/home/arif/AQMDir/master')
AQM_WORKING_DIR = getattr(settings, 'AQM_WORKING_DIR', '/home/arif/AQMDir/working')
AQM_PYTHON_BIN = getattr(settings, 'AQM_PYTHON_BIN', '/usr/bin/python')
AQM_CERT_CERT = getattr(settings, 'AQM_CERT_CERT', './cert/cert.pem')
AQM_CERT_KEY = getattr(settings, 'AQM_CERT_KEY', './cert/key.pem')
AQM_CERT_CACERT = getattr(settings, 'AQM_CERT_CACERT', './cert/cacert.pem')