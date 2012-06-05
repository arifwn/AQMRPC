
import threading

class BaseThreadProc(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def progress(self, info_str):
        pass
    
    def done(self):
        exit()
        
    def run(self):
        pass
    
class SampleThreadProc(BaseThreadProc):
    def __init__(self):
        BaseThreadProc.__init__(self)
        
    def run(self):
        import  time
        
        for i in range(100):
            time.sleep(0.1)
            self.progress("Tick: {0}".format(i))
            print 'tick', i
            if self.abort:
                print "Aborting..."
                break
        
        self.done()
		