
import re,warnings,urllib3,json
from elasticsearch.exceptions import NotFoundError
from elastic_transport import SecurityWarning

from datetime import datetime
from src.utils.funcs import defOptimized
from src.utils.errors import CodeError

from elasticsearch import AsyncElasticsearch

import config

# 忽略一些警告
# warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=SecurityWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def connetES(cls):
    if hasattr(cls, 'connect_setting'):
        es,indexname                    = cls.connect_setting
    else:
        name                            = cls.INDEX_NAME or re.sub('([a-z0-9])([A-Z])', r'\1_\2', cls.__name__[1:])
        indexname                       = f'{config.ES_INDEX_PREFIX}{name.lower()}'
        attrxname                       = f'ES_CONNECT_{name.upper()}'
        if hasattr(config, attrxname):
            connect_setting             = getattr(config, attrxname)
        else:
            connect_setting             = config.ES_CONNECT_DEFAULT
        es                              = AsyncElasticsearch(**connect_setting)
        cls.connect_setting             = es,indexname
        index_exists                    = await es.indices.exists(index=indexname)
        if not index_exists:
            await es.indices.create(index=indexname, body=cls.MAPPING)
    return es,indexname

class ESModel(dict):
    INDEX_NAME                          = None
    
    def __init__(self, *args, **kwargs):
        super(ESModel, self).__init__(*args, **kwargs)
        self._deep_property()

    @classmethod
    async def afrom(cls,_id=None,_must=False,_source=None,**match):
        es,indexname                    = await connetES(cls)
        if _id == None and not match:
            raise CodeError(f'缺少查询数据!')
        if _id == None:
            query                       = {'bool':{"must":[]}}
            for k,v in match.items():
                query['bool']['must'].append({"term": {k: v}})
            body                        = {
                "query"                 : query,
                "size"                  : 1,
            }
            if _source:
                body['_source']         = _source
            response                    = await es.search(
                index                   = indexname,
                body                    = body,
            )
            hits                        = response['hits']['hits']
            if hits:
                data                    = hits[0]['_source']
                data['_id']             = hits[0]['_id']
                return cls(**data)
            elif _must:
                raise CodeError(f'数据不存在')
            else:
                return None
        else:
            try:
                if isinstance(_source, list):
                    res                 = await es.get(index=indexname, id=_id,_source=_source)
                elif isinstance(_source, dict) and _source.get('excludes'):
                    res                 = await es.get(index=indexname, id=_id,_source_excludes=_source['excludes'])
                else:
                    res                 = await es.get(index=indexname, id=_id)
                data                    = res['_source']
                data['_id']             = res['_id']
                return cls(**data)
            except NotFoundError as e:
                if _must:
                    raise CodeError(f'数据不存在!')
                else:
                    return None

    @classmethod
    def defData(cls):
        data                            = {}
        for key,item in cls.MAPPING['mappings']['properties'].items():
            if key in cls.DEFAULT_ATTRVALUES:
                data[key]               = cls.DEFAULT_ATTRVALUES[key]
            elif item['type'] in ['keyword','text']:
                data[key]               = ''
            elif item['type'] in ['integer']:
                data[key]               = 0
            elif item['type'] in ['float']:
                data[key]               = 0.0
            elif item['type'] in ['boolean']:
                data[key]               = False
            else:
                data[key]               = None
        return data
        
    @classmethod
    async def virtual(cls,**data):
        data['virtual']                 = True
        return await cls.create(**data)

    @classmethod
    async def create(cls,refresh=False,virtual=False,_id=None,**attrs):
        data                            = cls.defData()
        data                            = defOptimized(attrs,**data)
        if virtual:
            return cls(**data)
        es,indexname                    = await connetES(cls)
        if not data.get('created',None):
            data['created']             = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not data.get('updated',None):
            data['updated']             = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res                             = await es.index(index=indexname, body=data, refresh=refresh,id=_id)
        data['_id']                     = res['_id']
        return cls(**data)

    @classmethod
    async def refreshIndex(cls):
        es,indexname                    = await connetES(cls)
        await es.indices.refresh(index=indexname)

    @classmethod
    async def upsetMany(cls,refresh=False,_id=None,**body):
        es,indexname                    = await connetES(cls)
        if _id:
            response                    = await es.update(index=indexname, id=_id, body={"doc":body}, refresh=refresh)
        else:
            response                    = await es.update_by_query(index=indexname,body=body,params={"refresh":refresh})
        return response.get('updated',0)

    # 更新属性
    async def upset(self,refresh=False,**data):
        update                          = {
            'updated'                   : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        for key,item in self.__class__.MAPPING['mappings']['properties'].items():
            if data.get(key,None)!=None:
                update[key]             = data[key]
        es,indexname                    = await connetES(self.__class__)
        await es.update(index=indexname, id=self._id, body={"doc":update}, refresh=refresh)
        self.update(update)
        return self

    # 删除数据
    async def destroy(self,refresh=False):
        es,indexname                    = await connetES(self.__class__)
        await es.delete(index=indexname, id=self._id, refresh=refresh, ignore=[404])
        return True
    
    # 数据脱敏
    def desensitization(self,attrs=None):
        data                            = {}
        for k,v in self.items():
            if k in self.__class__.PRIVACY_ATTRIBUTES:
                continue
            if attrs and k not in attrs:
                continue
            data[k]                     = v
        return self.__class__(**data) 

    @classmethod
    async def search(cls,**options)->tuple[list[dict], int]:
        es,indexname                    = await connetES(cls)
        response                        = await es.search(index=indexname, body=options)
        if response.get('timed_out',False):
            raise Exception('查询超时')
        list                            = []
        for item in response['hits']['hits']:
            item['_source']['_id']      = item['_id']
            item['_source']['_score']   = item.get('_score',None)
            list.append(cls(**item['_source']))
        return list,response['hits']['total']['value']
   
    @classmethod
    async def count(cls,**options):
        es,indexname                    = await connetES(cls)
        response                        = await es.count(index=indexname, body=options)
        if response.get('timed_out',False):
            raise Exception('统计超时')
        return response['count']
    
    @classmethod
    async def aggs(cls,aggs,size=0,**options):
        es,indexname                    = await connetES(cls)
        body                            = {**{'size':size,'aggs':aggs},**options}
        response                        = await es.search(index=indexname, body=body)
        if response.get('timed_out',False):
            raise Exception('聚合超时')
        return response['aggregations']

    @classmethod
    async def destroyMany(cls,_id=None,refresh=False,**options):
        es,indexname                    = await connetES(cls)
        if _id:
            response                    = await es.delete(index=indexname, id=_id, refresh=refresh, ignore=[404])
            return response['_shards']['successful']
        elif options:
            response                    = await es.delete_by_query(index=indexname, body=options,conflicts="proceed")
            return response['deleted']
        else:
            return False

    def __getattr__(self, name):
        return self.get(name,None)
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        if key in self:
            del self[key]

    def _deep_property(self):
        pass    
