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
import time
import logging
from os import path
from cStringIO import StringIO

import interprocess_lock

stdout_buffer = None
stderr_buffer = None
runner = None
socketobj = None
arguments = {}


class ExecutableRunner(threading.Thread):
    '''A thread to run another executable and wait until it finished'''
    def __init__(self, target, rundir, stdout_buffer, stderr_buffer):
        threading.Thread.__init__(self)
        self.rundir = rundir
        self.target = target
        self.stdout_buffer = stdout_buffer
        self.stderr_buffer = stderr_buffer
        self.daemon = True
        self.name = 'RunnerThread'
    
    def run(self):
        logging.info('target start')
        self.child = subprocess.Popen([self.target], stderr=self.stderr_buffer, 
                                      stdout=self.stdout_buffer, stdin=subprocess.PIPE)
        self.child.wait()
        stdout_buffer.flush()
        logging.info('target finished')
    
    def terminate(self):
        '''terminate child process'''
        logging.info('trying to kill %d' % self.child.pid)
        try:
            self.child.terminate()
        except Exception as err:
            logging.exception('cannot terminate child process!')


class ServerThread(threading.Thread):
    '''A thread that wait for connection to the unix socket'''
    def __init__(self, s):
        threading.Thread.__init__(self)
        self.socket = s
        self.daemon = True
        self.name = 'ServerThread'
    
    def run(self):
        while True:
            logging.info('waiting for connection...')
            self.socket.listen(3)
            
            try:
                conn, addr = self.socket.accept()
            except KeyboardInterrupt:
                logging.exception('exit')
                exit()
                
            logging.info('get new connection!')
            handler = ConnectionHandler(conn, addr)
            handler.start()
        


class ConnectionHandler(threading.Thread):
    '''
    A thread that handle command processing from a single socket connection
    '''
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
                logging.exception('exit')
                exit()
            
            if not command: break
            logging.info('received command: %s' % command)
            if command == 'exit':
                self.conn.send('ok')
                runner.terminate()
                break
            if command == 'close':
                self.conn.send('ok')
                break
            self.conn.send(process(command))
        self.conn.close()
        logging.info('connection closed')


def process(command):
    global stdout_buffer
    global stderr_buffer
    global arguments
    global runner
    
    if command == 'flush_log':
        stdout_buffer.flush()
        stderr_buffer.flush()
        return 'ok'
    elif command == 'status':
        return json.dumps(arguments)
    elif command == 'wait':
        # let's wait till we died
        while 1:
            time.sleep(10)
    elif command == 'terminate':
        # terminate running executable
        if runner is not None:
            runner.terminate()
        return 'ok'
    
    return 'error'

def daemonize(pidpath):
    logging.debug('demonized!')
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) 
    except OSError, e: 
        logging.error('fork #1 failed: %d (%s)' % (e.errno, e.strerror)) 
        sys.exit(1)

    os.setsid() 
    os.umask(0) 
    
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            logging.info('daemon PID %d' % pid) 
            sys.exit(0) 
    except OSError, e: 
        logging.error('fork #2 failed: %d (%s)' % (e.errno, e.strerror)) 
        sys.exit(1) 
    
    pid = str(os.getpid())
    pid_file = open(pidpath, 'w')
    pid_file.write(str(pid))
    pid_file.close()

        
def cleanup(args):
    global stdout_buffer
    global stderr_buffer
    

#    socket path should be removed before binding if it already exist,
#    if it removed when shutting down like this, there is a chance that
#    we can't rebind to this path later
      
#    socket_path = path.join(args.rundir, args.socket)
#    try:
#        os.remove(socket_path)
#    except OSError:
#        pass

    try:
        os.remove(args.pidfile)
    except OSError:
        pass
    try:
        stdout_buffer.flush()
        stdout_buffer.close()
    except:
        pass
        
    try:
        stderr_buffer.flush()
        stderr_buffer.close()
    except:
        pass
        

def runserver(args):
    global stdout_buffer
    global stderr_buffer
    global runner
    global socketobj
    
    if args.lockfile is None:
        lock = None
    else:
        logging.debug('acquiring lock file: %s' % args.lockfile)
        lock = interprocess_lock.FLockRLock(open(args.lockfile, 'a'))
        lock_acquired = lock.acquire(blocking=0)
    
    stdout_buffer = open(args.stdout, 'w')
    stderr_buffer = open(args.stderr, 'w')
    logging.debug('stdout: %s' % args.stdout)
    logging.debug('stderr: %s' % args.stderr)
    logging.debug('rundir: %s' % args.rundir)
    logging.debug('target: %s' % args.target)
    logging.debug('socket: %s' % args.socket)
    logging.debug('pid file: %s' % args.pidfile)
    
    runner = ExecutableRunner(args.target, args.rundir, stdout_buffer, stderr_buffer)
    runner.start()
    
    socket_path = path.join(args.rundir, args.socket)
    
    socketobj = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(socket_path)
    except OSError:
        pass
    
    socketobj.bind(socket_path)
    svr = ServerThread(socketobj)
    svr.start()
    if lock is not None:
        if lock_acquired:
            lock.release()
            logging.debug('lock file released')
    runner.join()    
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run target program as daemon.')
    parser.add_argument('--target', help='target executable')
    parser.add_argument('--socket', help='unix socket path')
    parser.add_argument('--rundir', help='run directory')
    parser.add_argument('--stdout', help='stdout log')
    parser.add_argument('--stderr', help='stderr log')
    parser.add_argument('--runnerlog', help='runner log')
    parser.add_argument('--pidfile', help='pid file')
    parser.add_argument('--lockfile', help='lock file')
    parser.add_argument('--id', help='identifier')
    parser.add_argument('--debug', action='store_true', dest='debug', default=False,
                        help='debug mode')
    
    args = parser.parse_args()
    arguments['target'] = args.target
    arguments['rundir'] = args.rundir
    arguments['id'] = args.id
    arguments['socket'] = args.socket
    arguments['stdout'] = args.stdout
    arguments['stderr'] = args.stderr
    arguments['runnerlog'] = args.runnerlog
    arguments['pidfile'] = args.pidfile
    arguments['debug'] = args.debug
    if (args.target is None) or (args.rundir is None) or \
       (args.id is None) or (args.socket is None) or \
       (args.stdout is None) or (args.stderr is None):
        print 'check your arguments!'
        parser.print_usage()
        exit(1)
    
    if args.debug is False and args.runnerlog is None:
        print 'you need to specify --runnerlog <log path>'
        exit(1)
    
    if args.debug is False and args.pidfile is None:
        print 'you need to specify --pidfile <pid file path>'
        exit(1)
    
    os.chdir(args.rundir)
    atexit.register(cleanup, args)
    
    logformat = '%(asctime)-15s [%(levelname)-7s] [%(threadName)-12s] [%(module)s] [line %(lineno)-4d] %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=logformat)
    else:
        logging.basicConfig(filename=args.runnerlog, level=logging.DEBUG, format=logformat)
    
    logging.info('runner started')
    if args.debug is False:
        daemonize(args.pidfile)
        
    runserver(args)
    logging.info('runner finished')
    