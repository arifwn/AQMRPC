'''
Created on Jul 10, 2011

@author: arif
'''

import hashlib
import os
import base64

salt1 = '1qs8fjr0x'
salt2 = 'kjnHJ9876'

def get_encryped_pid():
    ''' Return encrypted pid '''
    tmp = "%s%d%s" % (salt1, os.getpid(), salt2)
    m = hashlib.sha512(tmp)
    digest = m.digest()
    return base64.b64encode(digest)

def solve_encripted_pid(hash):
    ''' solve encrypted pid '''
    process_list = [(int(p), c) for p, c in [x.rstrip('\n').split(' ', 1) for x in os.popen('ps h -eo pid:1,command')]]
    hashd = base64.b64decode(hash)
    
    for pid in process_list:
        tmp = "%s%d%s" % (salt1, pid[0], salt2)
        m = hashlib.sha512(tmp)
        pid_hash = m.digest()
        if pid_hash == hashd:
            return pid[0]
    return None

if __name__ == '__main__':
    print os.getpid()
    hash =  get_encryped_pid()
    pid = solve_encripted_pid(hash)
    print pid