'''
Created on Sep 28, 2011

@author: Arif
'''
import xmlrpclib

if __name__ == '__main__':
    s = xmlrpclib.ServerProxy('http://localhost:8080')

    print "test()"
    print ">>", s.test_defer()
    