from datetime import datetime, timedelta, timezone

from src.super.controllers import OrganizationController

from src.entity.ECommissionBill import ECommissionBill

from src.utils.errors import CodeError


class Commission(OrganizationController):

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        status                          = post.get('status','')
        year                            = post.get('year')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        organization_id                 = self.organization._id
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": organization_id}}
            ]},
        }
        if year:
            query["bool"]["must"].append({"range": {"month": {
              "gte"         : f"{year}-01",
              "lte"         : f"{year}-12",
            }}})
        else:
            await ECommissionBill.refresh(organization_id=organization_id)
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
        list,total                      = await ECommissionBill.search(query=query,track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},
        
