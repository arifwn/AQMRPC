#!/usr/bin/env python
'''
Created on Feb 28, 2012

@author: arif
'''
import cStringIO
import argparse
import socket
import os
import subprocess
from os import path

def process(command):
    if command == 'flush_log':
        return 'ok'
    return 'error'

def daemonize(flag):
    print flag
    if flag:
        print 'demonized!'
    else:
        print 'not demonized!'

def runserver(args):
    os.chdir(args.rundir)
    f = open('log.txt', 'w')
    
    subprocess.Popen(['./wrf.exe'], stderr=f, stdout=f)
    
    socket_path = path.join(args.rundir, 'socket_ctrl')
    
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(socket_path)
    except OSError:
        pass
    
    running = True
    s.bind(socket_path)
    while running:
        print 'waiting for connection...'
        s.listen(1)
        conn, addr = s.accept()
        print 'connected'
        while 1:
            command = conn.recv(1024)
            if not command: break
            print 'received:', command
            if command == 'exit':
                running = False
                conn.send('ok')
                break
            if command == 'close':
                conn.send('ok')
                break
            conn.send(process(command))
        conn.close()
        print 'connection closed'
    print 'mainloop exit'
    try:
        os.remove(socket_path)
    except OSError:
        pass
        

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Run target program as daemon.')
    parser.add_argument('--target', help='target executable')
    parser.add_argument('--rundir', help='run directory')
    parser.add_argument('--debug', help='debug mode', type=bool, default=False)
    
    args = parser.parse_args()
    
    daemonize(args.debug)
    runserver(args)
    