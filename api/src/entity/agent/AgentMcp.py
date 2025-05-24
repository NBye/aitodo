from src.entity.EChatMessage import EChatMessage
from src.entity.EUserActionAgent import Agent
from src.entity.EFile import EFile

from src.utils.funcs import log
from src.entity.agent.tools import Parameters

class AgentMcp(Agent):
    def __init__(self,rname:str,parameters:object,action_id:str=None,**data):
        super().__init__(**data)
        self.action_id                  = action_id
        self.rname                      = rname
        self.parameters                 = Parameters(**parameters)

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        if self.action_id and (not self.action or self.action_id != self.action._id):
            from src.entity.EUserAction import EUserAction
            self.action                 = await EUserAction.afrom(_id=self.action_id)
        if not self.action:
            self.output                 = '找不到mcp 配置'
        else:    
            result                      = await self.action.call_mcp(self.rname,arguments)
            contents                    = []
            for t in result.content:
                if t.type == 'text':
                    contents.append(t.text)
                else:
                    log(f'{self.rname} 未支持的返回: {str(type(t))}')
            self.output                     = '\n'.join(contents)
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