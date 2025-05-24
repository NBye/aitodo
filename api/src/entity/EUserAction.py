from __future__ import annotations
import time,json
from typing import List, Dict

from src.super.ESModel import ESModel
from src.entity.EUserActionAgent import Agent

from src.utils.U62Id import U62Id

from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import config

class EUserAction(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        'enabled'                       : True,
        'support'                       : {
            'PC'                        : True,
            'Mac'                       : True,
            'Web'                       : True,
            'Android'                   : True,
            'IOS'                       : True,
        },
        'agent_list'                    : [],
        'settings'                      : {},
        'type'                          : 'custom',
    }
    MAPPING                             = {
        "settings"                      : {
            "index"                     : {
                "refresh_interval"      : "1s",
            }
        },
        "mappings"                      : {
            "dynamic"                   : "false", 
            "properties"                : {
                "user_id"               : {"type": "keyword"},      # AI用户ID
                "organization_id"       : {"type": "keyword"},     

                "name"                  : {"type": "text"},
                "description"           : {"type": "text"},
                "query_vector"          : {"type": "dense_vector", "dims": 1024,"similarity": "cosine",}, # 余弦相似cosine|点积dot_product
                "query_tokens"          : {"type": "integer"},

                "support"               : {"type": "object"},

                "type"                  : {"type": "keyword"},      # mpc | custom

                "agent_list"            : {"type": "object", "enabled": False},
                "settings"              : {"type": "object", "enabled": False}, #mpc 配置

                "enabled"               : {"type": "boolean"},

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,refresh=True,virtual=False,user=None,organization=None,**attrs):
        if organization==None:
            from src.entity.EOrganization import EOrganization
            organization                = await EOrganization.afrom(_id=attrs.get('organization_id',None),_must=True) 
        # vector,tokens                   = await organization.text_to_vector(f'{attrs.get("name","")}\n{attrs.get("description","")}')
        # attrs['query_vector']           = vector
        # attrs['query_tokens']           = tokens
        return await super().create(refresh=refresh,virtual=virtual,**attrs)
   
    async def upset(self,refresh=False,organization=None,**data):
        from src.entity.EOrganization import EOrganization
        if organization==None:
            organization                = await EOrganization.afrom(_id=self.organization_id,_must=True) 
        name                            = data.get("name","") or self.name
        description                     = data.get("description","") or self.description
        # vector,tokens                   = await organization.text_to_vector(f'{name}\n{description}')
        # data['query_vector']           = vector
        # data['query_tokens']           = tokens
        return await super().upset(refresh=refresh,**data)

    async def saveAgent(self,agent_list:list=[]):
        agent_list                      = [Agent.init(**item) for item in agent_list]
        lists                           = [*agent_list]
        while(len(lists)):
            a                           = lists.pop()
            if not a.get('name'):
                a['name']               = U62Id.generate(8)
            del a['chat']
            del a['user']
            del a['organization']
            del a['action']
            lists                       += [*a.get('children',[])]
        await self.upset(agent_list=agent_list)
        return self

    async def call_mcp(self,name,arguments):
        # print('> call_mcp',name,arguments)
        server_params                   = StdioServerParameters(**self.settings)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print(f'session.call_tool({name}, {arguments}) ')
                return await session.call_tool(name, arguments) 
        
