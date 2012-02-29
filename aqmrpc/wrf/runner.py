#!/usr/bin/env python
'''
Created on Feb 28, 2012

@author: arif
'''
import argparse
import socket
import os
import subprocess
import atexit
import threading
import json
from os import path
from cStringIO import StringIO

file_buffer = None
running = True
arguments = {}


class ExecutableRunner(threading.Thread):
    def __init__(self, target, rundir, file_output):
        threading.Thread.__init__(self)
        self.rundir = rundir
        self.target = target
        self.file_output = file_output
        self.daemon = True
    
    def run(self):
        child = subprocess.Popen([self.target], stderr=self.file_output, stdout=self.file_output)
        child.wait()
        file_buffer.flush()
        print 'runner finished'


class ConnectionHandler(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.daemon = True
    
    def run(self):
        global running
        while 1:
            try:
                command = self.conn.recv(1024)
            except KeyboardInterrupt:
                print 'exit'
                exit()
            
            if not command: break
            print 'received:', command
            if command == 'exit':
                running = False
                self.conn.send('ok')
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

def daemonize(flag):
    print flag
    if flag:
        print 'demonized!'
    else:
        print 'not demonized!'
        
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
    global running
    
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
    
    running = True
    s.bind(socket_path)
    while running:
        print 'waiting for connection...'
        s.listen(1)
        
        try:
            conn, addr = s.accept()
        except KeyboardInterrupt:
            print 'exit'
            exit()
            
        print 'connected'
        handler = ConnectionHandler(conn, addr)
        handler.start()
        
    print 'mainloop exit'
        

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
    
    daemonize(args.debug)
    runserver(args)
    