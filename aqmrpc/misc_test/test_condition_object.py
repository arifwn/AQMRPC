'''
Created on Jan 25, 2012

@author: arif
'''
import thread
import threading
import time

cv = threading.Condition()

def loop(arg):
    while True:
        cv.acquire()
        print "wait!"
        cv.wait()
        print 'got notified!'

t = thread.start_new_thread(loop, ('test',))

time.sleep(2)

for i in range(10):
    cv.acquire()
    cv.notify_all()
    cv.release()
    time.sleep(1)
    