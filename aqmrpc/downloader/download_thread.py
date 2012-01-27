'''
Created on Sep 30, 2011

@author: Arif
'''
import threading
import Queue
import logging


_thread_instance = None


class ConsumerThread(threading.Thread):
    '''Download every url in queue object'''
    
    _queue_obj = Queue.Queue()
    _continue_running = True
    _logger = logging.getLogger('Download Consumer Thread')
    queue_file = None
    
    def reinit(self):
        self._continue_running = True
        self._queue_obj = Queue.Queue()
    
    def put(self, item):
        '''put an item in the queue. Will block if queue is full. 
        But the queue is unlimited so...'''
        self._queue_obj.put(item)
    
    def put_nowait(self, item):
        '''put an item in the queue. 
        if queue is full it will throw an exception.'''
        self._queue_obj.put_nowait(item)
        
    def backup_queue(self, backup_filename=None):
        '''backup queue data to a file'''
        import pickle
        
        queue_file = self.queue_file
        if backup_filename is not None:
            queue_file = backup_filename
        
        if queue_file is None:
            return False
        
        queue_list = []
        keep_going = True
        while keep_going:
            try:
                data = self._queue_obj.get(False)
                queue_list.append(data)
            except:
                keep_going = False
        
        if len(queue_list) > 0:
            res = False
            try:
                with open(queue_file, 'wb') as f:
                    pickle.dump(queue_list, f)
                    res = True
            except:
                res = False
            return res
        else:
            return False
    
    def restore_queue(self, backup_filename=None):
        '''restore the queue from a backup file'''
        import pickle
        queue_file = self.queue_file
        if backup_filename is not None:
            queue_file = backup_filename
        
        if queue_file is None:
            return False
        
        res = False
        queue_list = []
        
        try:
            with open(queue_file, 'rb') as f:
                queue_list = pickle.load(f)
                res = True
        except:
            res = False
        
        if res == False:
            return False
        
        if type(queue_list) != list:
            return False
        
        for data in queue_list:
            self.put(data)
        
        return True
    
    def stop(self):
        '''signal the thread to stop'''
        self._continue_running = False
        self._logger.debug('stopping thread...')
    
    def do_run(self, return_on_finish=False):
        '''call this instead of start() to run the task in current thread'''
        while self._continue_running:
            skip = False
            try:
                data = self._queue_obj.get(timeout=3)
            except:
                skip = True
            if skip:
                if return_on_finish:
                    self._continue_running = False
                self._logger.debug('no data. skipping...')
                continue
            res = self.process_data(data)
            self._queue_obj.task_done()
            if res == False:
                self._logger.debug('processing fail! '
                                   'putting the data back to the queue...')
                self.put(data)
            
        self._logger.debug('thread stopped...')
    
    def run(self):
        self.do_run()
    
    def process_data(self, data):
        '''TODO: process retrived data from queue'''
        self._logger.debug('processing data: %s', data)
        print data
        return True


def get_download_thread():
    '''Return an instance of ConsumerThread'''
    global _thread_instance
    thread_ready = False
    
    try:
        thread_ready = _thread_instance.is_alive()
    except:
        thread_ready = False
    
    if thread_ready == False:
        _thread_instance = ConsumerThread()
        _thread_instance.start()
    
    return _thread_instance


def stop_thread():
    '''TODO: save unfinished queue to be restored later'''
    global _thread_instance
    try:
        _thread_instance.stop()
    except:
        pass


if __name__ == '__main__':
    import time
    logging.basicConfig(level=0, format='%(asctime)s | %(levelname)s | '
                        '%(message)s | %(name)s | %(pathname)s | %(lineno)s')
    t = get_download_thread()
    t.put('halo0')
    t.put('halo1')
    t.put('halo2')
    t.put('halo3')
    
    time.sleep(1)
    stop_thread()
    t.join()
    