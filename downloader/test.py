'''
Created on Sep 30, 2011

@author: Arif
'''
import unittest


class Test(unittest.TestCase):
    def test_dummy(self):
        self.assertEqual(1, 1)


class TestQueue(unittest.TestCase):
    
    def test_queue(self):
        import Queue
        import pickle
        q = Queue.Queue()
        q.put(1)
        q.put(2)
        q.put(3)
        
        s = pickle.dumps(q)
        t = pickle.loads(s)
        
        var1 = q.get()
        var2 = t.get()
        self.assertEqual(var1, var2)
        
        var1 = q.get()
        var2 = t.get()
        self.assertEqual(var1, var2)
        
        var1 = q.get()
        var2 = t.get()
        self.assertEqual(var1, var2)
        

def serialize_queue(file,queue_obj):
    '''serialize queue data to a file'''
    import pickle

    queue_file = file
    
    if queue_file is None:
        return False
    
    queue_list = []
    keep_going = True
    while keep_going:
        try:
            data = queue_obj.get(False)
            queue_list.append(data)
        except:
            keep_going = False
    
    if len(queue_list) > 0:
        res = True
        with open(queue_file, 'wb') as f:
            try:
                pickle.dump(queue_list, f)
                res = True
            except:
                res = False
        return res
    else:
        return False

def restore_queue(backup_filename):
    import pickle
    import Queue
    
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
    
    q = Queue.Queue()
    for data in queue_list:
        q.put(data)
    
    return q

def test1():
    import Queue
    q = Queue.Queue()
    q.put({'haha': 1, 'what': '???'})
    q.put({'haha': 2, 'what': '***'})
    q.put({'haha': 3, 'what': '!!!'})
    
    res = serialize_queue('test.txt', q)
    print 'serialized', res
    r = restore_queue('test.txt')
    print 'restore', r
    keep_going = True
    while keep_going:
        try:
            data = r.get(False)
            print data
        except Exception, e:
            keep_going = False
            print e

if __name__ == '__main__':
#    import sys;sys.argv = ['', 'Test.test_dummy']
#    unittest.main()
    test1()
    