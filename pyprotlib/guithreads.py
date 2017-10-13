import threading, queue
from inspect import isfunction
class Threader(threading.Thread):
    '''
    Class for creation threads to make calculations
    independent on GUI thread
    '''
    def __init__(self, func, *args,**kargs):

        threading.Thread.__init__(self)
        self.daemon = True
        self.func=func
        self.args=args
        self.kargs=kargs
        self.start()
        
    def run(self):
        return self.func(*self.args,**self.kargs)

def execqueue(root, que, tasknum=5, period=200):
    '''
    Function which is called every <period> msec to check <que> queue
    and execute functions from it, <tasknum> in a row
    line 'root.after(0, execqueue,<que>)' must be before mainlooping gui.
    Objects in queue can be: 1) function 2) (func, <arguments>)
    '''
    for i in range(tasknum):
        try:
            obj=que.get(block=False)
        except queue.Empty:
            break
        else:
            if isfunction(obj):
                obj() #call function without arguments
            elif type(obj) in (list,tuple):
                func,*args=obj
                func(*args)
            else:
                raise Exception('Not proper element in Queue object')
    root.after(period, execqueue, root, que)
