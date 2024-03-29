'''
Created on March 19, 2012

Adapted from http://code.activestate.com/recipes/577395-multiprocess-safe-logging-file-handler-interproces/

@author: arif
'''
import logging
import os
import sys
import fcntl
import threading

#
# Python 2.x or 3.x?
try:
    # 2.x (including < 2.6)
    from thread import get_ident as get_thread_ident
except ImportError:
    # 3.x
    def get_thread_ident(get_current_thread=threading.current_thread):
        return get_current_thread().ident


#
# Abstract classes
#

class MultiprocessRLock(object):
    '''Interprocess and interthread recursive lock (abstract class).'''

    def __init__(self):
        self._threading_lock = threading.Lock()
        self._owner = None
        self._count = 0

    def __repr__(self):
        return '<%s owner=%s count=%d>' % (self.__class__.__name__,
                                           self._owner, self._count)

    def _interprocess_lock_acquire(self, blocking):  # abstract method
        # the implementing function should return:
        # * True on success
        # * False on failure (applies to non-blocking mode)
        raise NotImplementedError

    def _interprocess_lock_release(self):  # abstract method
        raise NotImplementedError

    @staticmethod
    def _get_me(getpid=os.getpid, get_thread_ident=get_thread_ident):
        return '%d:%d' % (getpid(), get_thread_ident())

    def acquire(self, blocking=1):
        me = self._get_me()
        if self._owner == me:
            self._count += 1
            return True
        if not self._threading_lock.acquire(blocking):
            return False
        acquired = False
        try:
            acquired = self._interprocess_lock_acquire(blocking)
        finally:
            if not acquired:
                # important to be placed within the finally-block
                self._threading_lock.release()
            else:
                self._owner = me
                self._count = 1
        return acquired

    __enter__ = acquire

    def release(self):
        if self._owner != self._get_me():
            raise RuntimeError('cannot release un-acquired lock')
        self._count -= 1
        if not self._count:
            self._owner = None
            self._interprocess_lock_release()
            self._threading_lock.release()

    def __exit__(self, *args, **kwargs):
        self.release()



class MultiprocessFileHandler(logging.FileHandler):
    '''Multiprocess-safe logging.FileHandler replacement (abstract class).'''

    def createLock(self):  # abstract method
        '''Create a lock for serializing access to the underlying I/O.'''
        raise NotImplementedError



class LockedFileHandler(MultiprocessFileHandler):
    '''File-locking based logging.FileHandler replacement (abstract class).'''

    def __init__(self, filename, mode='a', encoding=None, delay=0):
        '''Open the specified file and use it for logging and file locking.'''
        if delay:
            raise ValueError('cannot initialize LockedFileHandler'
                             ' instance with non-zero delay')
        # base classe's __init__() calls createLock() method before setting
        # self.stream -- so we have to mask that method temporarily:
        self.createLock = lambda: None
        MultiprocessFileHandler.__init__(self, filename, mode, encoding)
        del self.createLock  # now unmask...
        self.createLock()    # ...and call it



class FLockRLock(MultiprocessRLock):
    '''flock-based MultiprocessRLock implementation.'''

    def __init__(self, lockfile):
        MultiprocessRLock.__init__(self)
        self.lockfile = lockfile

    def _interprocess_lock_acquire(self, blocking,
                                   flock=fcntl.flock,
                                   flags=(fcntl.LOCK_EX | fcntl.LOCK_NB,
                                          fcntl.LOCK_EX),
                                   exc_info=sys.exc_info):
        try:
            flock(self.lockfile, flags[blocking])
        except IOError:
            # Python 2.x & 3.x -compatibile way to get
            # the exception object: call sys.exc_info()
            if exc_info()[1].errno in (11, 13):
                return False  # <- applies to non-blocking mode only
            raise
        else:
            return True

    def _interprocess_lock_release(self, flock=fcntl.flock,
                                   LOCK_UN=fcntl.LOCK_UN):
        flock(self.lockfile, LOCK_UN)



class FLockFileHandler(LockedFileHandler):
    '''LockedFileHandler implementation using FLockRLock.'''

    def createLock(self):
        '''Create a lock for serializing access to the underlying I/O.'''
        self.lock = FLockRLock(self.stream)


def open_temp_file(path=None, mode='a'):
    if path is None:
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='a')
        f.close()
        return open(f.name, mode)
    else:
        return open(path, mode)

if __name__ == '__main__':
    import os
    lock_file = open_temp_file()
    lock_file_path = lock_file.name
    print 'lock:', lock_file_path
    
    lock = FLockRLock(lock_file)
    lock.acquire()
    if os.fork():
        #parent
        raw_input('type any key and enter to release lock:')
        lock.release()
        print 'parent: lock released!'
    else:
        #child
        clock = FLockRLock(open(lock_file_path, 'a'))
        print 'child: waiting for lock'
        clock.acquire()
        print 'child: lock acquired'
        clock.release()
    
    