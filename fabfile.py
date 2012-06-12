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

def get_all_files(directory, ext='.py'):
    import os
    
    ext_index = -len(ext)
    file_list = []
    
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f[ext_index:] == ext:
                file_list.append(os.path.join(root, f))
    
    return file_list

def count_line():
    ''' Count total line number of select files.
        find . -name '*.py' | xargs wc -l
    '''
    
    from cStringIO import StringIO
    
    f = {}
    name = 'aqmrpc'
    f['%s_py' % name] = get_all_files(name, '.py')
    f['%s_html' % name] = get_all_files(name, '.html')
    f['%s_js' % name] = get_all_files(name, '.js')
    f['%s_coffee' % name] = get_all_files(name, '.coffee')
    f['%s_less' % name] = get_all_files(name, '.less')
    
    name = 'rest'
    f['%s_py' % name] = get_all_files(name, '.py')
    f['%s_html' % name] = get_all_files(name, '.html')
    f['%s_js' % name] = get_all_files(name, '.js')
    f['%s_coffee' % name] = get_all_files(name, '.coffee')
    f['%s_less' % name] = get_all_files(name, '.less')
    
    name = 'servercon'
    f['%s_py' % name] = get_all_files(name, '.py')
    f['%s_html' % name] = get_all_files(name, '.html')
    f['%s_js' % name] = get_all_files(name, '.js')
    f['%s_coffee' % name] = get_all_files(name, '.coffee')
    f['%s_less' % name] = get_all_files(name, '.less')
    
    exclude_list = []
    
    file_list_nonfiltered = []
    file_list = []
    for key, val in f.iteritems():
        if len(val) > 0:
            file_list_nonfiltered.extend(val)
    
    for f in file_list_nonfiltered:
        skip = False
        for exclude in exclude_list:
            if exclude in f:
                skip = True
        if skip:
            continue
        file_list.append(f)
    
    file_list_buffer = StringIO()
    
    file_list_buffer.write('wc -l ')
    
    for f in file_list:
        file_list_buffer.write(f)
        file_list_buffer.write(' ')
        
    cmd = file_list_buffer.getvalue()
    
    if len(file_list) > 0:
        local(cmd)
    

def update_deployment():
    '''Update deployment code.'''
    
    deployment_target = '~/AQMSystem/deploy/aqmrpc'
    local('rm -rf %s/aqmrpc' % deployment_target)
    local('cp -rf aqmrpc %s/' % deployment_target)
    
    local('rm -rf %s/rest' % deployment_target)
    local('cp -rf rest %s/' % deployment_target)
    
    local('rm -rf %s/servercon' % deployment_target)
    local('cp -rf servercon %s/' % deployment_target)
    
    local('rm -rf %s/twisted' % deployment_target)
    local('cp -rf twisted %s/' % deployment_target)
    
    local('cp -rf fabfile.py %s/' % deployment_target)
    local('cp -rf manage.py %s/' % deployment_target)
    local('cp -rf servicemaker.py %s/' % deployment_target)
    