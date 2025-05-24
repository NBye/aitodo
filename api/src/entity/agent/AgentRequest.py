import json,httpx
from typing import List, Dict
from datetime import datetime

from src.utils.U62Id import U62Id
from src.utils.CDict import CDict
from src.utils.errors import CodeError

from src.entity.EChatMessage import EChatMessage
from src.entity.EUserActionAgent import Agent

from src.entity.agent.tools import Parameters

import config

class AgentRequestHeader(CDict):
    key : str
    val : str

class AgentRequest(Agent):
    def __init__(self,url:str,method:str='post',headers:list=[],parameters:dict={},metadata:bool=False,template='',**data):
        super().__init__(**data)
        self.metadata                   = metadata
        self.url                        = url
        self.method                     = method.lower()
        self.headers                    = [AgentRequestHeader(**item) for item in headers]
        self.parameters                 = Parameters(**parameters)
        self.template                   = template

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        headers                         = {}
        for h in self.headers:
            headers[h['key'].lower()]   = h['val']
        if True:
            headers['user-id']          = message.user_id
        if self.user:
            headers['assistant-id']     = self.user._id
        if self.chat:
            headers['chat-id']          = self.chat._id
            headers['organization-id']  = self.chat.organization_id
        # print('before',json.dumps(arguments,indent=4, ensure_ascii=False))
        # 补齐缺省字段
        queue                           = [*self.parameters.properties]
        while len(queue):
            propertie                   = queue.pop(0)
            if propertie.path == None:
                propertie.path          = []
            if propertie.type=='object':
                for p in propertie.properties:
                    p.path              = propertie.path + [propertie.key]
                    queue.append(p)
            else:
                current                 = arguments
                for k in propertie.path:
                    if isinstance(current.get(k,None), dict)==False:
                        current[k]      = {}
                    current             = current[k]
                if propertie.default=='':
                    continue
                if current.get(propertie.key):
                    continue
                default                 = await self.template_render(str(propertie.default),
                    strict              = True,
                    message             = message,
                    messages            = messages,
                    parameters          = arguments,
                )
                try:
                    if propertie.type == 'number':
                        current[propertie.key]  = float(default)
                    elif propertie.type == 'integer':
                        current[propertie.key]  = int(default)
                    elif propertie.type == 'object':
                        current[propertie.key]  = json.loads(default)
                    else:
                        current[propertie.key]  = default
                except BaseException as e:
                        current[propertie.key]  = default
        if self.metadata:
            arguments['metadata']      = self.chat.metadata
        # print('after',json.dumps(arguments,indent=4, ensure_ascii=False))
        if self.url.startswith("http"):
            url                         = self.url
        elif self.url.startswith("/"):
            url                         = f"{config.HOST}{self.url}"
        else:
            url                         = f"{config.HOST}/{self.url}"

        async with httpx.AsyncClient(verify=False) as client:
            response                    = await getattr(client,self.method)(url,headers=headers, json=arguments)
            if response.status_code != 200:
                raise CodeError(f'Agent Request Error[{response.status_code}] {url}\n{response.text or '请求失败'}')
            if 'json' in response.headers.get('content-type',''):
                self.output                 = CDict(response.json())
            else:
                self.output                 = response.text
            if self.template.strip():
                self.output                 = await self.template_render(self.template,
                    message                 = message,
                    messages                = messages,
                    parameters              = arguments,
                )
        return self.output

    def toFunction(self):
        return {
            "type"                      : "function",
                "function"              : {
                    "name"              : self.name,
                    "description"       : self.description,
                    "parameters"        : self.parameters.toJSON()
                }
            }
