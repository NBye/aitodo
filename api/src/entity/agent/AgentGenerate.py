import time,json,traceback
from typing import List, Dict
from datetime import datetime

from src.utils.U62Id import U62Id
from src.utils.CDict import CDict

from src.entity.EChatMessage import EChatMessage

from src.entity.EUserActionAgent import Agent
from src.entity.agent.tools import Parameters


class AgentGenerate(Agent):
    def __init__(self, input:str,model:list=None,parameters:dict={},**data):
        super().__init__(**data)
        self.input                      = input
        self.model                      = model if model and len(model) else None
        self.parameters                 = Parameters(**parameters)

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        try:
            self.output                 = await self.template_render(self.input,strict=True,
                message                 = message,
                messages                = messages,
                parameters              = arguments,
            )
            if self.model:
                content                     = ''
                logtime                     = int(time.time() * 1000)
                async for data,_ in self.user.execute_model('Generate.generate',prompt=self.output,stream=False,temperature=0.1,model=self.model):
                    content                 += data['content']
                self.output                 = content
        except BaseException as e:
            self.output                 = f'Agent调用异常: ```\n{str(e)}\n{traceback.format_exc()}\n```'
        return self.output.strip()

    def toFunction(self):
        return {
            "type"                      : "function",
                "function"              : {
                    "name"              : self.name,
                    "description"       : self.description,
                    "parameters"        : self.parameters.toJSON()
                }
            }
