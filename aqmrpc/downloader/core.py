'''
Created on Oct 1, 2011

@author: Arif
'''
import cookielib
import urllib
import urllib2
import os.path


class UrlClient():
    proxy_handler = None
    cookie_jar = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cookie_jar)
    
    url_opener = urllib2.build_opener(cookie_handler)
    
    def set_proxy(self, url):
        '''url: http://user:passwd@cache.itb.ac.id:8080 '''
        proxy_list = {'http': url,
                      'https': url,
                      'ftp': url}
        self.proxy_handler = urllib2.ProxyHandler(proxy_list)
        self.url_opener = urllib2.build_opener(self.cookie_handler, 
                                               self.proxy_handler)
    
    def ping(self, url, params_dict=None):
        '''open specified url and discard returned data but persist the 
        cookies.
        use case: the server require session cookies set before you can 
        download a resource. you can specify login url and login data, then 
        retrieve the session cookies with this method. Any cookies set within 
        this methods will be persisted and used in every subsequent request.
        params_dict: dictionary of parameters to be sent to server. If you 
        specify this argument, this function will use http post instead of 
        http get.'''
        
        if params_dict is None:
            params = None
        else:
            params = urllib.urlencode(params_dict)
        request = urllib2.Request(url, data=params)
        r = self.url_opener.open(request)
        r.read()
    
    def download(self, url, save_path, filename=None, params_dict=None):
        '''Download the specified url and save it to save_path. If filename 
        is not None, it will save it to savepath/filename.'''
        
        if params_dict is None:
            params = None
        else:
            params = urllib.urlencode(params_dict)
        request = urllib2.Request(url, data=params)
        if filename is not None:
            path = os.path.abspath(os.path.join(save_path, filename))
        else:
            path = os.path.abspath(save_path)
        path = os.path.normpath(path)
        r = self.url_opener.open(request)
        with open(path, 'wb') as f:
            while 1:
                data = r.read(1024)
                if data == '':
                    break
                f.write(data)
        
    
def test1():
    params = urllib.urlencode({'email': 'arif@ftsl.itb.ac.id', 
                               'passwd': 'banDung', 'action': 'login'})
    print params
    url = urllib2.Request('https://dss.ucar.edu/cgi-bin/login', data=params)
    path = 'test.html'
    print url
    
#    proxy_list = {'http': 'http://user:passwd@cache.itb.ac.id:8080',
#                  'https': 'http://user:passwd@cache.itb.ac.id:8080',}
#    proxy_handler = urllib2.ProxyHandler(proxy_list)
    
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), proxy_handler)
    r = opener.open(url)
    
    with open(path, 'w') as f:
        while 1:
            data = r.read(1024)
            if data == '':
                break
            f.write(data)
    print r.info()
    
    print 'cookie'
#    cj.extract_cookies(r, url)
    for c in cj:
        print c.name, ' : ', c.value
    
#    print 'now downloading...'
#    url = 'http://dss.ucar.edu/dsszone/ds083.2/grib2/2011/2011.01/fnl_20110101_00_00'
#    path = 'test.bin'
#    r = opener.open(url)
#    with open(path, 'wb') as f:
#        while 1:
#            data = r.read(1024)
#            if data == '':
#                break
#            f.write(data)
#    print r.info()


def test2():
    c = UrlClient()
    login_params = {'email': 'arif@ftsl.itb.ac.id', 
                    'passwd': 'banDung', 'action': 'login'}
    c.ping('https://dss.ucar.edu/cgi-bin/login', login_params)
    for cookie in c.cookie_jar:
        print cookie.name, ' : ', cookie.value
    
    url = 'http://dss.ucar.edu/dsszone/ds083.2/grib2/2011/2011.01/fnl_20110101_00_00'
    c.download(url, 'test.bin')
    print 'done!'


def test3():
    c = UrlClient()
    url = 'http://www.google.com/images/nav_logo89.png'
    c.download(url, 'test.png')
    print 'done!'


def test_proxy():
    c = UrlClient()
    url = 'http://www.google.com/images/nav_logo89.png'
    c.set_proxy('http://hexanouns:siskacool@cache.itb.ac.id:8080')
    c.download(url, 'test.png')
    print 'done!'

    
if __name__ == '__main__':    
    test_proxy()
    