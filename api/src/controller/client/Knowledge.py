from src.super.controllers import OrganizationController

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EKnowledgeBucket import EKnowledgeBucket
from src.entity.EKnowledge import EKnowledge

from src.entity.EFile import EFile
from src.entity.ECache import ECache
from src.utils.funcs import md5,pdf_to_markdown,docx_to_markdown
from src.utils.errors import CodeError
import re

class Knowledge(OrganizationController):

    async def bucketCreate(self):
        data                            = await self._check_data(None,[
            ('name',            [4,20],     None,   '类型名称需要4~20个字符'),
            ('description',     [0,200],     None,   '描述需要0~200个字符'),
        ])
        vector,tokens                   = await self.organization.text_to_vector(f"{data['name']}\n{data['description']}")
        data['query_vector']            = vector
        data['query_tokens']            = tokens
        knowledge_bucket                = await EKnowledgeBucket.create(**data,
            organization_id             = self.organization._id,
        )
        del knowledge_bucket['query_vector']
        return {'knowledge_bucket':knowledge_bucket},'创建成功',

    async def bucketSearch(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[
                {"term": {"organization_id": self.organization._id}}
            ]},
        }
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"name": keyword}},
                        {"match": {"description": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await EKnowledgeBucket.search(query=query,track_total_hits=10000,sort=sort_list,_source={'excludes':['query_vector']},**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def bucketInfo(self):
        post                            = await self.get_post()
        knowledge_bucket_id             = post.get('knowledge_bucket_id','')
        if not knowledge_bucket_id:
            raise CodeError('缺少必要参数',400)
        knowledge_bucket                = await EKnowledgeBucket.afrom(_id=knowledge_bucket_id,_source={'excludes':['query_vector']})
        if not knowledge_bucket:
            raise CodeError('未找到类型信息',404)
        if knowledge_bucket.organization_id!=self.organization._id:
            raise CodeError('没有权限查看',403)
        return {'knowledge_bucket':knowledge_bucket},

    async def bucketUpset(self):
        knowledge_bucket                = (await self.bucketInfo())[0]['knowledge_bucket']
        data                            = await self._check_data(None,[
            ('name',            [4,20],     None,   '类型名称需要4~20个字符'),
            ('description',     [0,200],     None,   '描述需要0~200个字符'),
        ])
        vector,tokens                   = await self.organization.text_to_vector(f"{data['name']}\n{data['description']}")
        data['query_vector']            = vector
        data['query_tokens']            = tokens
        await knowledge_bucket.upset(**data)
        del knowledge_bucket['query_vector']
        return {'knowledge_bucket':knowledge_bucket},
        
    async def bucketDestroy(self):
        knowledge_bucket                = (await self.bucketInfo())[0]['knowledge_bucket']
        await knowledge_bucket.destroy()
        await EKnowledge.destroyMany(query={'term':{'knowledge_bucket_id':knowledge_bucket._id}})
        return {},'删除成功'
        
    async def importText(self):
        knowledge_bucket                = (await self.bucketInfo())[0]['knowledge_bucket']
        data                            = await self._check_data(None,[
            ('knowledge_bucket_id',     [0,20],     None,      '知识库ID'),
            ('file_id',                 [0,20],     None,      '文件ID'),
            ('text',                    [0,20000],  None,       '知识需要2万个字以内，如果太长请自行切割'),
        ])
        list                            = []
        async for knowledge in self.organization.import_knowledge(user=self.user,**data):
            del knowledge['query_vector']
            list.append(knowledge)
        return {'list':list},'导入成功',
    
    async def upload(self):
        knowledge_bucket                = (await self.bucketInfo())[0]['knowledge_bucket']
        files                           = await self.get_files()
        total                           = 0
        data                            = dict(
            knowledge_bucket_id         = knowledge_bucket._id,
            text                        = ''
        )
        for k,fs in files.items():
            print(fs.content_type)
            if 'pdf' in fs.content_type.lower():
                data['text']            = await pdf_to_markdown(fs=fs)
            elif 'doc' in fs.content_type.lower():
                data['text']            = await docx_to_markdown(fs=fs)
            elif 'word' in fs.content_type.lower():
                data['text']            = await docx_to_markdown(fs=fs)
            else:
                continue
            async for knowledge in self.organization.import_knowledge(user=self.user,**data):
                del knowledge['query_vector']
                total                   += 1
        return {'total':total},'导入成功',

    async def search(self): 
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        knowledge_bucket_id             = post.get('knowledge_bucket_id','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": self.organization._id}},
                {"term": {"knowledge_bucket_id": knowledge_bucket_id}},
                
            ]},
        }
        if keyword: 
            vector,tokens               = await self.organization.text_to_vector(keyword)
            query["bool"]["must"].append({"knn": {
                "field"                 :"query_vector",
                "query_vector"          : vector,
                "num_candidates"        : 10000
            }})
            sort_list                   = []
        list,total                      = await EKnowledge.search(query=query,track_total_hits=10000,sort=sort_list,_source={'excludes':['query_vector']},**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        knowledge_id                    = post.get('knowledge_id','')
        if not knowledge_id:
            raise CodeError('缺少必要参数',400)
        knowledge                       = await EKnowledge.afrom(
            _id                         = knowledge_id,
            _source={'excludes':['query_vector']}
        )
        if not knowledge:
            raise CodeError('未找到知识信息',404)
        if knowledge.organization_id != self.organization._id:
            raise CodeError('无权限查看',403)
        return {'knowledge':knowledge},

    async def upset(self):
        knowledge                       = (await self.info())[0]['knowledge']
        data                            = await self._check_data(None,[
            ('text',                    [1,256],    None,   '知识需要1~256千个字符，如果太长请自行切割'),
        ])
        vector,tokens                   = await self.organization.text_to_vector(data['text'])
        data['query_vector']            = vector
        data['query_tokens']            = tokens
        data['size']                    = len(data['text'].encode('utf-8'))*8
        await knowledge.upset(**data)
        del knowledge['query_vector']
        return {'knowledge':knowledge},
        
    # async def destroy(self):
    #     knowledge                       = (await self.info())[0]['knowledge']
    #     await knowledge.destroy()
    #     return {},'删除成功'

