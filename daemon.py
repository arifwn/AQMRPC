'''
Created on Sep 28, 2011

@author: Arif
'''

import sys
import os
import time
import atexit
import SocketServer
from signal import SIGTERM 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from server import AsyncXMLRPCServer
import pidencrypt
import interface

class Daemon:
    """
    RPC Server Daemon.
    """
    
    def __init__(self, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', 
                 address='localhost', port=8080):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.address = address
        self.port = port
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
        
        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 
        
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
    
        # redirect standard file descriptors
        
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
    def start(self):
        """
        Start the daemon
        """
        # Start the daemon
        self.daemonize()
        sys.stdout.write("Daemon start...\n")
        self.run()

    def stop(self, pid):
        """
        Stop the daemon
        """
        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            pass

    def restart(self, pid):
        """
        Restart the daemon
        """
        self.stop(pid)
        self.start()
        
    def status(self):
        """
        RPC handler for status checking
        """
        return pidencrypt.get_encryped_pid()
    
    def run(self):
        """
        
        """
        # Create server
        server = AsyncXMLRPCServer((self.address, self.port), requestHandler=SimpleXMLRPCRequestHandler)
        server.register_introspection_functions()
        
        # Register status() function
        server.register_function(self.status)
        
        # Register instance containing methods to be exposed
        server.register_instance(interface.Interface())
    
        # Run the server
        server.serve_forever()

if __name__ == '__main__':
    pass
