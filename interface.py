'''
Created on Sep 28, 2011

@author: Arif
'''

class Interface():
    def create_job(self, job_type, job_id):
        pass
    
    def open_job(self, job_id):
        pass
    
    def remove_job(self, job_id):
        pass
    
    def run_job(self, job_id):
        pass
    
    def pause_job(self, job_id):
        pass
    
    def cancel_job_run(self, job_id):
        pass
    
    def resume_job(self, job_id):
        pass
    
    def get_job_status(self, job_id):
        pass
    
    def get_job_info(self, job_id):
        pass
    