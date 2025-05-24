import asyncio,queue
from collections.abc import AsyncIterator
from typing import Callable

class AsyncIteratorQuque:
    def __init__(self,*args):
        self.iterators                  = []
        self.results                    = queue.Queue()
        for iterator in args:
            self.join(iterator)

    def join(self, iterator:AsyncIterator):
        self.iterators.append(iterator)
        asyncio.create_task(self._consume_iterator(iterator))

    async def _consume_iterator(self,iterator:AsyncIterator):
        async for result in iterator:
            self.results.put(result)
        self.iterators.remove(iterator)

    async def consume(self,wait:Callable=None):
        while self.iterators or not self.results.empty():
            while not self.results.empty():
                yield self.results.get()
            if delay:=await wait() if wait else None:
                yield delay
            await asyncio.sleep(0.001)