from quart import request
from src.super.controllers import BaseController

from src.entity.EDocument import EDocument

from src.utils.errors import CodeError

class Document(BaseController):

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"enabled": True}},
            ]},
        }
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"nickname": keyword}},
                        {"match": {"abstract": keyword}},
                        {"match": {"text": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await EDocument.search(query=query,track_total_hits=10000,sort=sort_list,_source={'excludes':['text']},**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        document_id                     = post.get('document_id','')
        if not document_id:
            raise CodeError('缺少必要参数',400)
        document                        = await EDocument.afrom(
            _id                         = document_id,
        )
        if not document:
            raise CodeError('未找到文档',404)
        return {'document':document},

    async def upset(self):
        document                        = (await self.info())[0]['document']
        data                            = await self._check_data(None,[
            ('title',               [4,20],     None,   '类型名称需要4~20个字符'),
            ('abstract',            [0,200],     None,   '内容200个字符以内'),
            ('text',                [0,100000],  None,   '内容10万个字符以内'),
            ('enabled',             [0,10],     None,   ''),
        ])
        await document.upset(**data)
        return {'document':document},
        
    async def destroy(self):
        document                        = (await self.info())[0]['document']
        await document.destroy()
        return {},'删除成功'

