'''
Created on Mar 16, 2012

@author: arif
'''
from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.context_managers import cd, lcd
import datetime

env.hosts = []
project_dir = ''

# ~/workspace/deploy/ : temporary directory
# ~/workspace/NewsSite/ : svn root of the project

def dump_data():
    local('python manage.py dumpdata --indent=4 > aqmrpc/fixtures/initial_data.json')
