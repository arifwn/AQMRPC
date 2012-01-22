'''
Created on Sep 28, 2011

@author: Arif
'''

from twisted.web import xmlrpc

class Interface(xmlrpc.XMLRPC):
    
    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        
    def xmlrpc_create_job(self, job_type, job_id):
        pass
    
    def xmlrpc_open_job(self, job_id):
        pass
    
    def xmlrpc_remove_job(self, job_id):
        pass
    
    def xmlrpc_run_job(self, job_id):
        pass
    
    def pause_job(self, job_id):
        pass
    
    def xmlrpc_cancel_job_run(self, job_id):
        pass
    
    def xmlrpc_resume_job(self, job_id):
        pass
    
    def xmlrpc_get_job_status(self, job_id):
        pass
    
    def xmlrpc_get_job_info(self, job_id):
        pass
    
    def xmlrpc_test(self):
        return 'Hello, World!'
    