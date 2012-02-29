#!/usr/bin/env python
'''
Created on Feb 28, 2012

@author: arif
'''
import argparse
import socket
import os
import sys
import subprocess
import atexit
import threading
import json
from os import path
from cStringIO import StringIO

file_buffer = None
runner = None
arguments = {}


class ExecutableRunner(threading.Thread):
    def __init__(self, target, rundir, file_output):
        threading.Thread.__init__(self)
        self.rundir = rundir
        self.target = target
        self.file_output = file_output
        self.daemon = True
    
    def run(self):
        self.child = subprocess.Popen([self.target], stderr=self.file_output, stdout=self.file_output)
        self.child.wait()
        file_buffer.flush()
        print 'runner finished'
    
    def terminate(self):
        self.child.terminate()


class ServerThread(threading.Thread):
    def __init__(self, s):
        threading.Thread.__init__(self)
        self.socket = s
        self.daemon = True
    
    def run(self):
        while True:
            print 'waiting for connection...'
            self.socket.listen(3)
            
            try:
                conn, addr = self.socket.accept()
            except KeyboardInterrupt:
                print 'exit'
                exit()
                
            print 'connected'
            handler = ConnectionHandler(conn, addr)
            handler.start()
        


class ConnectionHandler(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.daemon = True
    
    def run(self):
        global runner
        while 1:
            try:
                command = self.conn.recv(1024)
            except KeyboardInterrupt:
                print 'exit'
                exit()
            
            if not command: break
            print 'received:', command
            if command == 'exit':
                self.conn.send('ok')
                try:
                    runner.terminate()
                except:
                    pass
                break
            if command == 'close':
                self.conn.send('ok')
                break
            self.conn.send(process(command))
        self.conn.close()
        print 'connection closed'

def process(command):
    global file_buffer
    global arguments
    
    if command == 'flush_log':
        file_buffer.flush()
        return 'ok'
    elif command == 'status':
        return json.dumps(arguments)
    
    return 'error'

def daemonize():
    print 'demonized!'
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    os.chdir("/") 
    os.setsid() 
    os.umask(0) 
    
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 


        
def cleanup(args):
    global file_buffer
    socket_path = path.join(args.rundir, 'socket_ctrl')
    try:
        os.remove(socket_path)
    except:
        pass
    try:
        file_buffer.close()
    except:
        pass
        

def runserver(args):
    global file_buffer
    global runner
    
    os.chdir(args.rundir)
    file_buffer = open('log.txt', 'w')
    print 'rundir:', args.rundir
    print 'target:', args.target
    
    runner = ExecutableRunner(args.target, args.rundir, file_buffer)
    runner.start()
    print 'runner started'
    
    socket_path = path.join(args.rundir, 'socket_ctrl')
    
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(socket_path)
    except:
        pass
    
    s.bind(socket_path)
    svr = ServerThread(s)
    svr.start()
    runner.join()    
        

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Run target program as daemon.')
    parser.add_argument('--target', help='target executable')
    parser.add_argument('--rundir', help='run directory')
    parser.add_argument('--id', help='identifier')
    parser.add_argument('--debug', help='debug mode', type=bool, default=False)
    
    args = parser.parse_args()
    arguments['target'] = args.target
    arguments['rundir'] = args.rundir
    arguments['id'] = args.id
    arguments['debug'] = args.debug
    
    atexit.register(cleanup, args)
    
    if not args.debug:
        daemonize()
    
    runserver(args)
    