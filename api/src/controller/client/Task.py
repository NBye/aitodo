from src.super.controllers import OrganizationController

from src.entity.ETask import ETask
from src.entity.EOrganization import EOrganization
from src.entity.EUser import EUser

from src.utils.errors import CodeError

class Task(OrganizationController):

    async def create(self):
        organization                    = await self._get_organization()
        data                            = await self._check_data(None,[
            ('title',                   [0,200],     None,   '描述需要0~200个文字'),
            ('description',             [2,2000],    None,   '请输入有效的时间字符串'),
            ('executor_user_id',        [10,50],     None,   '执行者ID必传'),
            ('cron_expr',               [0,50],      None,   '计划'),
            ('cron_enabled',            [0,50],      None,   '计划启用'),
            ('schedule_time',           [0,50],      None,   '时间'),
        ])
        executor                        = await EUser.afrom(_id=data['executor_user_id'])
        if not executor:
            raise CodeError('找不到执行者:' + data['executor_user_id'])
        task                            = await ETask.create(user=self.user,executor=executor,organization=self.organization,refresh=True,**data)
        return {'task':task},'创建成功',

    async def search(self):
        post                            = await self.get_post()
        organization                    = await self._get_organization()
        keyword                         = post.get('keyword','')
        executor_user_id                = post.get('executor_user_id','')
        user_id                         = post.get('user_id','')
        time_range                      = post.get('time_range')

        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool" : {"must":[
                {"term": {"organization_id": organization._id}},
            ]},
        }
        if executor_user_id:
            query["bool"]["must"].append({"term": {"executor_user_id": executor_user_id}})
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        if time_range and time_range[0] and time_range[1]:
            query["bool"]["must"].append({"range": {"created": {
              "gte"         : time_range[0],
              "lte"         : time_range[1],
            }}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"title": keyword}},
                        {"match": {"description": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await ETask.search(query=query,track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        user_ids                        = [t.executor_user_id for t in list]

        users,_                         = await EUser.search(query={'terms':{'_id':user_ids}},_source=['nickname','avatar','role'])
        usermap                         = {u._id:u for u in users}

        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
            list[i]['executor']         = usermap.get(e.executor_user_id)
        return {'list':list,'total':total},
        
    async def info(self):
        post                            = await self.get_post()
        organization                    = await self._get_organization()
        task_id                         = post.get('task_id','')
        if not task_id:
            raise CodeError('缺少必要参数',400)
        task                            = await ETask.afrom(
            _id                         = task_id,
        )
        if not task:
            raise CodeError('未找到任务',404)
        if task.organization_id != organization._id:
            raise CodeError('无权查看',403)
        return {'task':task},

    async def upset(self):
        task                            = (await self.info())[0]['task']
        data                            = await self._check_data(None,[
            ('title',                   [0,200],     None,   '描述需要0~200个文字'),
            ('description',             [2,2000],    None,   '请输入有效的时间字符串'),
            ('executor_user_id',        [10,50],     None,   '执行者ID必传'),
            ('enabled',                 [0,10],      None,   ''),
            ('cron_expr',               [0,50],      None,   '计划'),
            ('cron_enabled',            [0,50],      None,   '计划启用'),
            ('schedule_time',           [0,50],      None,   '时间'),
            ('status',                  [0,50],      None,   ''),
        ])
        if 'executor_user_id' in data:
            executor                    = await EUser.afrom(_id=data['executor_user_id'])
            if not executor:
                raise CodeError('找不到执行者:' + data['executor_user_id'])
            data['executor_user_role']  = executor.role
        else:
            executor                    = await EUser.afrom(_id=task['executor_user_id'])
        await task.upset(**data)
        organization                    = await self._get_organization()
        task['executor']                = executor
        await organization.event_publish('task-update',{"task":task})
        return {'task':task},'保存成功'
        
    async def destroy(self):
        task                          = (await self.info())[0]['task']
        await task.destroy()
        organization                    = await self._get_organization()
        await organization.event_publish('task-remove',{"task":task})
        return {},'删除成功'

