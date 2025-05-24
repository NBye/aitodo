from src.entity.EChat import EChat
import asyncio,json
from quart import request,Response

async def generate():
    for i in range(100): 
        await asyncio.sleep(1)  
        data = {'i':i}
        yield f"data: {json.dumps(data)}\n\n"
       
class Test():
    async def _async_init(self):
        pass
    async def t1(self,a,b,c):
        return {
            'a':a,
            'b':b,
            'c':c
        }

    async def t2(self,*ss):
        return str(ss)

    async def each(self):
        return Response(generate(), mimetype='text/event-stream')