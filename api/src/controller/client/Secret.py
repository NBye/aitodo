from src.super.controllers import OrganizationController

from src.entity.ESecret import ESecret
from src.entity.EOrganization import EOrganization

from src.utils.errors import CodeError

class Secret(OrganizationController):

    async def create(self):
        organization                    = await self._get_organization()
        count                           = await ESecret.count(query={'term':{'organization_id':organization._id}})
        if count>=50:
            raise CodeError('最多只能有50个密钥')
        data                            = await self._check_data(None,[
            ('description',             [4,20],     None,   '描述需要4~20个文字'),
            ('expired',                 [19,20],    None,   '请输入有效的时间字符串'),
            ('type',                    [0,20],     None,   ''),
            ('expired',                 [0,20],     None,   ''),
        ])
        secret                          = await ESecret.create(user=self.user,organization=organization,refresh=True,**data)
        return {'secret':secret},'创建成功',

    async def search(self):
        post                            = await self.get_post()
        organization                    = await self._get_organization()
        keyword                         = post.get('keyword','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": organization._id}},
            ]},
        }
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"description": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await ESecret.search(query=query,track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        organization                    = await self._get_organization()
        secret_id                       = post.get('secret_id','')
        if not secret_id:
            raise CodeError('缺少必要参数',400)
        secret                          = await ESecret.afrom(
            _id                         = secret_id,
        )
        if not secret:
            raise CodeError('未找到文档',404)
        if secret.organization_id != organization._id:
            raise CodeError('无权查看',403)
        return {'secret':secret},

    async def upset(self):
        secret                          = (await self.info())[0]['secret']
        data                            = await self._check_data(None,[
            ('description',             [4,20],     None,   '描述需要4~20个文字'),
            ('type',                    [0,20],     None,   ''),
            ('expired',                 [0,20],     None,   ''),
            ('enabled',                 [0,10],     None,   ''),
        ])
        await secret.upset(**data)
        return {'secret':secret},'保存成功'
        
    async def destroy(self):
        secret                          = (await self.info())[0]['secret']
        await secret.destroy()
        return {},'删除成功'

