from __future__ import annotations
import json,time,re,traceback
from typing import List, Dict
from src.utils.U62Id import U62Id

from src.utils.CDict import CDict
from src.utils.errors import CodeError
from src.utils.Template import Template
from src.utils.funcs import log
from src.utils.Datetime import Datetime

from src.entity.EChatMessage import EChatMessage

from src.entity.agent.tools import AgentLog,AgentMetadata


class Agent(CDict):
    def __init__(self,chat=None,user=None,organization=None,action=None,name=None,description='',decision='ai',disabled=False,children:list=[], **data):
        self.chat                       = chat                              # 使用的房间
        self.user                       = user                              # 使用的用户
        self.organization               = organization                      # Agent所属组织
        self.action                     = action                            # action 
        self.type                       = data.get('type','')
        self.name                       = name or U62Id.generate(8)         # 名称
        self.description                = description                       # 描述
        self.decision                   = decision                          # 决策模式 ai,auto
        self.disabled                   = disabled                          # 是否禁用
        self.children                   = [Agent.init(**{**item,**{'chat':chat,'user':user,'organization':organization}}) for item in children]

    @classmethod
    def init(cls,**data):
        # print(json.dumps(data,indent=4, ensure_ascii=False))
        if data['type']=='knowledge':
            from src.entity.agent.AgentKnowledge import AgentKnowledge
            return AgentKnowledge(**data)
        if data['type']=='request':
            from src.entity.agent.AgentRequest import AgentRequest
            return AgentRequest(**data)
        if data['type']=='generate':
            from src.entity.agent.AgentGenerate import AgentGenerate
            return AgentGenerate(**data)
        if data['type']=='docx':
            from src.entity.agent.AgentDocx import AgentDocx
            return AgentDocx(**data)
        if data['type']=='modelcall':
            from src.entity.agent.AgentModelcall import AgentModelcall
            return AgentModelcall(**data)
        if data['type']=='mcp':
            from src.entity.agent.AgentMcp import AgentMcp
            return AgentMcp(**data)
        # raise CodeError(f'不支持的Agent: {data["type"]}')
    
    async def template_render(self,template,strict=False,**data):
        try:
            data['output']              = self.output
            data['parent']              = {'output':self.parent.output}
            # print(json.dumps(data,indent=4, ensure_ascii=False))
            return await Template(template,
                metadata                = AgentMetadata(entity=self.chat),
                **data,
            )
        except BaseException as e:
            if strict:
                raise e
            return f"模板调用异常: ```\n{str(e)}\n{traceback.format_exc()}\n```"
    def toFunction(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def execute(self,message:EChatMessage,messages:list[EChatMessage],reply:EChatMessage,replys:list[EChatMessage],unique_cahce={}):
        async for data,prompt_tokens in self.executeChildren(message,messages,reply,replys=replys,unique_cahce=unique_cahce):
            yield data,prompt_tokens
        if reply.get('embeddings') or not reply.get('content'):
            if EChatMessage.contain_image([*messages,message]):
                model               = self.user.get_setting_model('visionmodel')
            else:
                model               = self.user.get_setting_model('textmodel')
            completion              = self.user.execute_model('Chat.send',
                model               = model,
                messages            = [*messages,message,*replys,*([reply] if reply.get('embeddings') else [])],
                stream              = True,
            )
            async for data,prompt_tokens in completion:
                yield data,prompt_tokens
        logdata                         = AgentLog('最终执行')
        logdata.append(await EChatMessage.transform_history(self.user,messages=[*messages,message,*replys,reply]))
        await reply.log(**logdata)
        

    # messages 包含了system
    async def executeChildren(self,message:EChatMessage,messages:list[EChatMessage],reply:EChatMessage,replys:list[EChatMessage],unique_cahce={}):
        tool_agent,hits_agent,installs  = {},[],{}
        # 1. 执行子集 Agent
        for agent in self.children:
            if not agent:
                continue                # 为开发实现Agent类型。
            agent.parent                = self
            if agent.disabled:
                continue
            installs[agent.name]        = agent.toFunction()
            if agent.decision == 'ai':
                tool_agent[agent.name]  = agent
            else:
                hits_agent.append((agent,{}))
        await reply.upset(tools=reply.tools.update(installs))
        # 2. 执行 tools Agent
        if tool_agent:
            completion                  = self.user.execute_model('Chat.send',
                model                   = self.user.get_setting_model('model'),
                messages                = [*messages,message,*replys,*([reply] if reply.get('embeddings') else [])],
                tools                   = [agent.toFunction() for agent in tool_agent.values()],
                stream                  = True,
                strict                  = True,
            )
            async for data,_ in completion:
                for name,arguments in data.get('tool_calls',[]):
                    if name in tool_agent:
                        hits_agent.append((tool_agent[name],arguments))
                yield data,_

        embeddings                      = []
        for agent,arguments in hits_agent:
            unique_key                  = agent.name+"_"+json.dumps(arguments)
            if unique_key in unique_cahce:
                continue
            unique_cahce[unique_key]      = True
            yield {
                'status'                : 'call_tools',
                'tokens'                : 0,
                'status_description'    : agent.description,
                "role"                  : self.user.role,
                "content"               : '',
            }, 0
            # 执行子集Agent
            agent.exetime               = int(time.time() * 1000)
            output                      = await agent.execute(message,messages,arguments=arguments)
            output                      = output if isinstance(output,str) else json.dumps(output,ensure_ascii=False)
            agent.endtime               = int(time.time() * 1000)
            agent.usetime               = agent.endtime - agent.exetime
            reply.tools[agent.name]['used'] = True
            # 存入日志
            logdata                 = AgentLog(agent.description)
            logdata.append(f"**参数:**\n\n```json\n{json.dumps(arguments,indent=4, ensure_ascii=False)}\n```")
            logdata.append(f"**返回:**\n\n{output}")
            await reply.log(**logdata)
            if not agent.children:
                # 嵌入结果
                embeddings.append({
                    'description'       : agent.description,
                    'arguments'         : arguments,
                    'output'            : output,
                    'exetime'           : agent.exetime,
                    'endtime'           : agent.endtime,
                    'usetime'           : agent.usetime,
                })
            else:
                if output:
                    message             = await message.copy()
                    message.content     = output
                async for child in agent.executeChildren(message,messages,reply,replys=replys,unique_cahce=unique_cahce):
                    yield child
        if hits_agent:
            await reply.upset(tools=reply.tools)
        if  embeddings:
            yield {
                "status"            : 'call_tools',
                "role"              : self.user.role,
                "content"           : '',
                "tokens"            : 0,
                "embeddings"        : embeddings,
            }, 0

        