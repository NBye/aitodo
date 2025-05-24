from typing import List
from collections.abc import Iterator
import threading,uuid,time
import queue

class ThreadIteratorQueue:
    def __init__(self):
        self.queue                      = queue.Queue()
        self.threads                    = []
        self.delayed                    = {}

    async def _iterator(self,iterator):
        async for item in iterator:
            self.queue.put(item)

    def join(self,iterator,_id=None):
        t                               = threading.Thread(target=self._iterator, args=(iterator,))
        t._id                           = _id
        t.start()
        self.threads.append(t)

    def wait_join(self,iterator,_id):
        t                               = threading.Thread(target=self._wait, args=(iterator,_id))
        t.start()

    def _wait(self,iterator,_id):
        while True:
            active                      = False
            for t in self.threads:
                if t._id==_id and t.is_alive():
                    active              = True
                    # print('[wait] queue _id:',t._id)
                    time.sleep(1)
                    break
            else:
                break
        return self.join(iterator,_id)  
        
    async def each(self):
        while True:
            if not self.queue.empty():
                yield self.queue.get()
            if len(self.threads)>0:
                t                       = self.threads.pop()
                if t.is_alive():
                    self.threads.append(t)
            else:
                break


