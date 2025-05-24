from src.super.controllers import BaseController

from src.entity.EUser import EUser
from src.entity.ECache import ECache
from src.entity.EOrganizationUser import EOrganizationUser
from src.utils.funcs import md5

class User(BaseController):

    async def login(self):
        post                            = await self.get_post()
        token, user, _                  = await EUser.login(str(post.get('type',None)),
            username                    = post.get('username',''),
            phone                       = post.get('phone',None),
            email                       = post.get('email',None),
            password                    = md5(post.get('password','')),
            token                       = post.get('token',None),

            phone_code_id               = post.get('phone_code_id',None),
            phone_code                  = post.get('phone_code','').upper(),
            
            email_code_id               = post.get('email_code_id',None),
            email_code                  = post.get('email_code','').upper(),
            
            img_code_id                 = post.get('img_code_id',None),
            img_code                    = post.get('img_code','').upper(),
        )
        return {'user':user,'token':token},'登录成功'

    async def info(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        user                            = await EUser.afrom(user_id)
        if user:
            user                        = user.desensitization()
        return {'user':user},

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        gender                          = post.get('gender','')
        birthday                        = post.get('birthday','')
        role                            = post.get('role','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[
                {"term": {"disabled": False}}
            ]},
        }
        if gender: 
            query["bool"]["must"].append({
                "term": {"gender": gender}
            })
        if role: 
            query["bool"]["must"].append({
                "term": {"role": role}
            })
        if birthday: 
            query["bool"]["must"].append({
                "range": {
                    "birthday": {
                        "gte": f"{birthday}-01-01",
                        "lte": f"{birthday}-12-31" 
                    }
                }
            })
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"nickname": keyword}},
                        {"match": {"introduction": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await EUser.search(query=query,_source={"excludes": ["introduction"]},sort=sort_list,track_total_hits=10000,**{'from':skip,'size':size})
        for i,user in enumerate(list):
            list[i]                     = user.desensitization()
        return {'list':list,'total':total},

