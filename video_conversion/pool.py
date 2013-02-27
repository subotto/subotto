# -*- coding: utf-8 -*-

# Code from http://code.activestate.com/recipes/577187-python-thread-pool/

from Queue import Queue
from threading import Thread

import os
import sys

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: func(*args, **kargs)
            except Exception, e: print e
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

if __name__ == '__main__':
    files = os.listdir('./dv')

    def convert_file(dv):
        theora = dv.replace('.dv', '.mkv')
        print 'Start conversion of %s -> %s' % (dv, theora)
        cmd = 'avconv -deinterlace -threads 1 -i dv/%s -acodec libmp3lame -vcodec libx264 -ab 256k -b 5000k x264/%s' % (dv, theora)
        print 'Executing %s' % (cmd)
        os.system(cmd)
        print 'Finished conversion of %s -> %s' % (dv, theora)

    pool = ThreadPool(6)
    
    for f in files:
        pool.add_task(convert_file, f)
    
    pool.wait_completion()
