from __future__ import annotations
import time,json

from src.utils.Redis import Redis
from datetime import datetime, timedelta

import config

class ECache():

    @classmethod
    async def setData(cls,index,timeout=3600*24,**data):
        data                            = json.dumps(data)
        await Redis().setex(index,timeout,data)

    @classmethod
    async def getData(cls,index,path=None):
        data                           = await Redis().get(index)
        if data==None:
            return None
        data                           = json.loads(data)
        if path==None:
            return data
        paths                           = path.split('.')
        while len(paths)>0:
            path                        = paths.pop()
            if isinstance(data, dict):
                data                    = data.get(path,None)
            else:
                return None
        return data

    @classmethod
    async def delData(cls,index):
        await Redis().delete(index)

    @classmethod
    async def getOnceData(cls,index,path=None):
        data                            = await cls.getData(index,path)
        await cls.delData(index)
        return data