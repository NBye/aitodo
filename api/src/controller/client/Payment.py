from src.super.controllers import OrganizationController

from src.entity.EPayment import EPayment

from src.utils.errors import CodeError

class Payment(OrganizationController):

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        status                          = post.get('status','')
        time_range                      = post.get('time_range')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": self.organization._id}}
            ]},
        }
        if time_range and time_range[0] and time_range[1]:
            query["bool"]["must"].append({"range": {"created": {
              "gte"         : time_range[0],
              "lte"         : time_range[1],
            }}})
        if status:
            query["bool"]["must"].append({"term": {"status": status}})
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
        list,total                      = await EPayment.search(query=query,track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        payment_id                      = post.get('payment_id','')
        if not payment_id:
            raise CodeError('缺少必要参数',400)
        payment                         = await EPayment.afrom(
            _id                         = payment_id,
        )
        if not payment:
            raise CodeError('未找到文档',404)
        return {'payment':payment},

