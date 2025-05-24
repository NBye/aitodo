from src.super.controllers import OrganizationController
import json,asyncio

from src.entity.EUserAction import EUserAction
from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.utils.funcs import defOptimized
from src.utils.errors import CodeError

from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import config

def tran_parameters(parameters,required=[],defs={}):
    properties                          = []
    for key,data in parameters.items():
        if isinstance(data,dict) and '$ref' in data:
            data                        = dict(
                default                 = data.get('default',''),
                description             = data.get('description',''),
                **defs.get(data['$ref'][8:])
            )
        properties.append({
            "bind"                      : "",
            "default"                   : "",
            "description"               : data.get('description',''),
            "enum"                      : [],
            "key"                       : key,
            "properties"                : tran_parameters(data.get('properties',{}),data.get('required',[]),defs),
            "required"                  : key in required,
            "type"                      : data.get('type','string')
        })
    return properties

async def mcp_tools(settings):
    server_params                       = StdioServerParameters(**settings)
    agent_list                          = []
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response                    = await asyncio.wait_for(session.list_tools(), timeout=2.0)
            for tool in response.tools:
                agent_list.append({
                    "type"              : 'mcp',
                    "decision"          : 'ai',
                    "action_id"         : '', # 空字符串跟随所属Action Mpc，否则指定Action Mpc
                    "rname"             : tool.name,
                    "description"       : tool.description,
                    "parameters"        : {
                        'type'          : 'object', 
                        "properties"    : tran_parameters(tool.inputSchema.get('properties',{}),tool.inputSchema.get('required',[]),tool.inputSchema.get('$defs',{}))
                    }
                })
    return agent_list

class Action(OrganizationController):
    VERIFY_LIST                         = []

    async def _check_permission(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        ou                              = await EOrganizationUser.afrom(user_id=user_id,organization_id=self.organization._id)
        if not ou:
            raise CodeError('无权限')
        user                            = await self.getUser(user_id)
        if not user or user.role != 'assistant':
            raise CodeError('无权限2')
        return True

    async def create(self):
        await self._check_permission()
        post                            = await self.get_post()
        data                            = await self._check_data(verify_list=[
            ('name',        [2,20],     None,   '标题2~20个字符'),
            ('description', [0,500],    None,   '描述500个字符以内'),
            ('support',     [0,512],    None,   '支持平台数据异常'),
            ('type',        [2,20],     None,   '能力类型不能为空'),
            ('settings',    [0,1024],   None,   '设置不能过长'),
        ])
        if 'settings' in data and isinstance(data['settings'], str):
            data['settings']            = json.loads(data['settings'])
        data['user_id']                 = post.get('user_id',None)
        data['organization_id']         = self.organization._id
        if data['type'] == 'mcp':
            agent_list                  = await mcp_tools(data['settings'])
        else:
            agent_list                  = []
        action                          = await EUserAction.create(organization=self.organization, **data)
        if data['type'] == 'mcp' and agent_list:
            await action.saveAgent(agent_list=agent_list)
        del action['query_vector']
        return {'action':action},

    async def info(self):
        post                            = await self.get_post()
        action_id                       = post.get('action_id',None)
        action                          = await EUserAction.afrom(_id=action_id,_source={'excludes':['query_vector']})
        if not action:
            raise CodeError('能力未找到')
        # if action.organization_id!=self.organization._id:
        #     return {},'无权限查看',403
        return {'action':action},

    async def upset(self):
        post                            = await self.get_post()
        data                            = await self._check_data(verify_list=[
            ('name',        [2,20],     None,   '标题2~20个字符'),
            ('description', [0,500],    None,   '描述500个字符以内'),
            ('support',     [0,512],    None,   '支持平台数据异常'),
            ('enabled',     [0,10],     None,   ''),
            ('type',        [2,20],     None,   '能力类型不能为空'),
            ('settings',    [0,1024],   None,   '设置不能过长'),
        ])
        if 'settings' in data and isinstance(data['settings'], str):
            data['settings']            = json.loads(data['settings'])
        action_id                       = post.get('action_id',None)
        action                          = await EUserAction.afrom(_id=action_id,_source={'excludes':['query_vector']})
        if not action:
            raise CodeError('能力未找到')
        if action.organization_id!=self.organization._id:
            raise CodeError('无权限查看',403)
        if 'type' in data and data['type'] == 'mcp':
            agent_list                  = await mcp_tools(data['settings'])
        else:
            agent_list                  = []
        if 'type' in data and data['type'] == 'mcp' and agent_list:
            agent_list                  = await mcp_tools(data['settings'])
            await action.saveAgent(agent_list=agent_list)
        await action.upset(**data)
        return {'action':action},'修改成功'

    async def saveAgent(self):
        post                            = await self.get_post()
        action_id                       = post.get('action_id',None)
        action                          = await EUserAction.afrom(_id=action_id,_source={'excludes':['query_vector']})
        if not action:
            raise CodeError('能力未找到')
        if action.organization_id!=self.organization._id:
            raise CodeError('无权限查看',403)
        agent_list                      = post.get('agent_list')
        await action.saveAgent(agent_list=agent_list)
        return {'action':action},'修改成功'

    async def search(self):
        post                            = await self.get_post()
        _source                         = post.get('_source','')
        keyword                         = post.get('keyword','')
        user_id                         = post.get('user_id','')
        supports                        = post.get('support','')
        enabled                         = post.get('enabled','')
        type                            = post.get('type','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[]},
        }
        if user_id:
            query["bool"]["must"].append({
                "term": {"user_id": user_id}
            })
        else:
            query["bool"]["must"].append({
                "term": {"organization_id": self.organization._id}
            })
        if isinstance(enabled, bool):
            query["bool"]["must"].append({
                "term": {"enabled": enabled}
            })
        if supports:
            for s in supports.split(','):
                query["bool"]["must"].append({
                    "term": {f"support.{s}": True}
                })
        if type:
            query["bool"]["must"].append({
                "term": {"type": type}
            })
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
        list,total                      = await EUserAction.search(query=query,_source=_source or {"excludes": ["query_vector","agent_list","agent_process"]},track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        for i,action in enumerate(list):
            list[i]                     = action.desensitization()
            if self.organization._id != action.organization_id:
                if 'agent' in list[i]:
                    del list[i]['agent']
        return {'list':list,'total':total},

    async def destroy(self):
        post                            = await self.get_post()
        action_id                       = post.get('action_id',None)
        action                          = await EUserAction.afrom(_id=action_id)
        if not action:
            raise CodeError('能力未找到')
        if action.organization_id!=self.organization._id:
            return {},'无权限查看',403
        await action.destroy()
        return {},'删除成功'