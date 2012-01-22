'''
Created on Sep 30, 2011

@author: Arif
'''
import logging
from aqmrpc import downloader

if __name__ == '__main__':
    logging.basicConfig(level=0, format='%(asctime)s | %(levelname)s | %(message)s | %(name)s | %(pathname)s | %(lineno)s')
    downloader.add_http('url', 'target_dir', 'filename', 'overwrite', 'auth', 'auth_method')
    downloader.stop()