'''
Created on Oct 3, 2011

@author: Arif
'''

import settings

class BaseModelJob():
    '''this is a base implementation of job processor.'''
    
    def __init__(self, job_id, client_id, client_mail, step=None):
        '''override this'''
        self.job_id = job_id
        self.client_id = client_id
        self.client_mail = client_mail
        
        self.step_ids = ['data_prep',
                         'preprocessor',
                         'model_run',
                         'postprocessor',
                         'plot_result']
        self.step_func = {'data_prep': self.__dummy_func,
                 'preprocessor': self.__dummy_func,
                 'model_run': self.__dummy_func,
                 'postprocessor': self.__dummy_func,
                 'plot_result': self.__dummy_func}
        self.current_step = 0
        
        # 0: not run yet, 1: success, -1: failed
        self.step_results = [0, 0, 0, 0, 0]
        
        # string describing model result, e.g. 'File not found'
        self.step_logs = ['', '', '', '', '']
    
    def __dummy_func(self):
        pass
    
    def notify_client(self):
        '''send message to client about the job's result'''
        #prepare message
        
        #send message
        pass
    
    def run_job(self):
        '''run the modeling job'''
        for i, step_id in enumerate(self.step_ids):
            if i < self.current_step:
                continue
            self.current_step = i
            
            func = self.step_func[step_id]
            result_flag = False
            result_string = None
            try:
                result_flag, result_string = func()
            except Exception, e:
                result_flag = False
                result_string = str(e)
            
            self.report_step_result(step_id, result_flag, result_string)
            if result_flag == False:
                break

def test():
    import downloader
    data = downloader.simple_url_request('http://www.arstechnica.com/')
    print data
    
if __name__ == '__main__':
    
    test()