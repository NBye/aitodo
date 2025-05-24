import json,re,time

from src.utils.CDict import CDict
from src.utils.errors import CodeError

class Propertie(CDict):
    def __init__(self, type, key, description='',bind='',required=True,default="", enum=[], properties:list=[]):
        self.key                        = key
        self.type                       = type.lower()
        self.description                = description
        self.default                    = default
        self.bind                       = bind
        self.properties                 = [Propertie(**p) for p in properties]
        self.required                   = required
        self.enum                       = enum
    def toJSON(self):
        data                            = {
            'type'                      : self.type,
            'description'               : self.description,
        }
        if len(self.enum):
            data['enum']                = self.enum
        if self.type == 'object':
            data['properties']          = {}
            data['required']            = []
            for p in self.properties:
                data['properties'][p.key]   = p.toJSON()
                if p.required:
                    data['required'].append(p.key)
        return data

class Parameters(CDict):
    def __init__(self, type='object', properties:list=[],**data):
        self.type                       = type.lower()
        self.properties                 = [Propertie(**p) for p in properties]

    def toJSON(self):
        data                            = {
            "type"                      : "object",
            "properties"                : {},
        }
        for p in self.properties:
            data['properties'][p.key]   = p.toJSON()
        required                        = []
        for p in self.properties:
            if p.required :
                required.append(p.key)
        if len(required) > 0:
            data['required']            = required
        return data


class AgentLog(CDict):
    def __init__(self,remark:str):
        self.time                       = int(time.time() * 1000)
        self.remark                     = remark
        self.list                       = []
        self.status                     = 'log'
    def append(self,text:str):
        self.list.append(text)

class AgentMetadata():
    def __init__(self,entity):
        if not hasattr(entity,'metadata'):
            raise CodeError(f'{str(type(entity))} 不支持 metadata。')
        if not isinstance(entity.metadata, CDict):
            entity.metadata             = CDict(entity.metadata or {})
        self.__entity                    = entity

    async def set(self,key,val):
        self.__entity.metadata[key]       = val
        await self.save()
        return val

    async def get(self,key=None):
        if not key:
            return self.__entity.metadata
        elif key in self.__entity.metadata:
            return self.__entity.metadata.get(key)
        else:
            return None

    async def delete(self,key):
        if key in self.__entity.metadata:
            del self.__entity.metadata[key]
        await self.save()

    async def update(self,data={}):
        maxsize                         = 2048
        self.__entity.metadata.update(data)
        if len(json.dumps(self.__entity.metadata).encode('utf-8')) > maxsize:
            raise CodeError(f'metadata 数据超过 {maxsize}字节, 保存失败!')
        await self.__entity.upset(metadata=self.__entity.metadata)
        return dict(**self.__entity.metadata)

    async def save(self,data={}):
        maxsize                         = 2048
        if len(json.dumps(data).encode('utf-8')) > maxsize:
            raise CodeError(f'metadata 数据超过 {maxsize}字节, 保存失败!')
        self.__entity.metadata          = data
        await self.__entity.upset(metadata=data)
        return data

    def __getattr__(self, key):
        if key.startswith('_'):
            return self.__dict__.get(key)
        return self.get(key)

    def __setattr__(self, key, val):
        if key.startswith('_'):
            self.__dict__[key]          = val
        else:
            self.set(key,val)
        return val

    def __delattr__(self, key):
        if not key.startswith('_'):
           self.delete(key) 
