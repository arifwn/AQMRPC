#!/usr/bin/env python

'''
Created on Jun 18, 2011

@author: arif
'''

import sys
import time
import os
import xmlrpclib
import pidencrypt
from daemon import Daemon
import settings

if __name__ == '__main__':
    # Do not use relative path!
    stdoutfile = os.getcwd() + '/stdout.txt'
    stderrfile = os.getcwd() + '/stderr.txt'
    address = 'localhost'
    port = settings.port
    
    daemon = Daemon(stdout=stdoutfile, stderr=stderrfile, address=address, port=port)
    
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            s = xmlrpclib.ServerProxy('http://localhost:%d'%port)
            try:
                pid = pidencrypt.solve_encripted_pid(s.status())
                daemon.stop(pid)
            except Exception, err:
                pass
        elif 'restart' == sys.argv[1]:
            s = xmlrpclib.ServerProxy('http://localhost:%d'%port)
            try:
                pid = pidencrypt.solve_encripted_pid(s.status())
                daemon.restart(pid)
            except Exception, err:
                print 'Stopped'
        elif 'status' == sys.argv[1]:
            s = xmlrpclib.ServerProxy('http://localhost:%d'%port)
            accessible = True
            try:
                s.status()
            except Exception, err:
                accessible = False
            
            if accessible:
                print "Running"
            else:
                print "Stopped"
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start | stop | restart | status" % sys.argv[0]
        sys.exit(2)
