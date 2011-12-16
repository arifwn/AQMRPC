'''
Created on Sep 30, 2011

@author: Arif

Implements producer-consumer mechanism to add and consume the download jobs'''

import logging
from downloader import download_thread

def add_url(url, save_path, filename=None, overwrite=False, url_params=None,
             proxy=None, setup_url=None, setup_params=None, teardown_url=None,
             teardown_params=None):
    '''Add specified url to a queue to be downloaded and saved to target_dir. 
    Return True for successful queue.
    Will cancel the download process if the file is already exist in target_dir, 
    unless you set overwrite=True.
    specify parameter dictionary in url_params. Use setup_url and teardown_url to
    make request before and after dowloading the file
    '''
    data = {'url': url, 'url_params': url_params, 'save_path': save_path, 
            'filename': filename, 'overwrite': overwrite, 'proxy': proxy,
            'setup_url': setup_url, 'setup_params': setup_params,
            'teardown_url': teardown_url, 'teardown_params': teardown_params}
    t = download_thread.get_download_thread()
    ret = False
    try:
        t.put_nowait(data)
        ret = True
    except:
        logger = logging.getLogger('downloader.add_http')
        logger.exception('Cannot append url to download queue!')
    return ret

def stop():
    download_thread.stop_thread()

def simple_url_request(url, params_dict=None, proxy=None):
    import urllib
    import urllib2
    if params_dict is None:
        params = None
    else:
        params = urllib.urlencode(params_dict)
    
    url_opener = urllib2.build_opener()
    if proxy is not None:
        proxy_list = {'http': url,
                      'https': url,
                      'ftp': url}
        proxy_handler = urllib2.ProxyHandler(proxy_list)
        url_opener = urllib2.build_opener(proxy_handler)
    
    request = urllib2.Request(url, data=params)
    r = url_opener.open(request)
    return r.read()
    