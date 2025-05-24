from src.super.controllers import OrganizationController

from src.entity.EDataBase import EDataBase

from src.utils.errors import CodeError

class Database(OrganizationController):

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        type                            = post.get('type','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": self.organization._id}}
            ]},
        }
        if type:
            query["bool"]["must"].append({"term": {"type": type}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"remark": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await EDataBase.search(query=query,track_total_hits=10000,sort=sort_list,_source={'excludes':['content']},**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        data_id                         = post.get('data_id','')
        if not data_id:
            raise CodeError('缺少必要参数',400)
        data                            = await EDataBase.afrom(
            _id                         = data_id,
        )
        if not data:
            raise CodeError('找不到数据',404)
        return data,

    async def upset(self):
        data                            = (await self.info())[0]
        upse                            = await self._check_data(None,[
            ('type',                    [4,20],      None,   '类型需要4~20个字符'),
            ('remark',                  [0,200],     None,   '备注200个字符以内'),
            ('content',                 [0,2000],    None,   '内容200个字符以内'),
        ])
        print(upse)
        await data.upset(**upse)
        return data,
        
    async def destroy(self):
        data                            = (await self.info())[0]
        await data.destroy()
        return {},'删除成功'


    async def groups(self):
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": self.organization._id}}
            ]},
        }
        aggs                            = await EDataBase.aggs({
            "types": {
                "terms": {
                    "field": "type",
                    "size": 100
                }
            }
        },query=query,size=0)
        list                            = []
        maps                            = {
            'voice_clone'   :{'icon':'icon-voice'   ,'name':'声音复刻','description':'语音克隆时，复刻的原始声音配置数据。'},
            'other'         :{'icon':'icon-database','name':'其他数据'},
        }
        for item in aggs['types']['buckets']:
            data                        = maps[item['key']] if item['key'] in maps else maps['other']
            list.append(dict(type=item['key'],count=item['doc_count'],**data,))
        return {'list':list},