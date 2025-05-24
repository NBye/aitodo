import time,json,traceback
from typing import List, Dict
from datetime import datetime

from src.utils.U62Id import U62Id
from src.utils.CDict import CDict

from src.entity.EChatMessage import EChatMessage
from src.entity.EFile import EFile

from src.entity.EUserActionAgent import Agent
from src.entity.agent.tools import Parameters


class AgentModelcall(Agent):
    def __init__(self, model:list,model_action:str,model_params:dict={},format_template='',**data):
        super().__init__(**data)
        self.model                      = model
        self.model_action               = model_action
        self.model_params               = Parameters(**model_params)
        self.format_template            = format_template

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        tokens_total                    = 0
        prompt_tokens_total             = 0
        self.output                     = await self.user.call_model(model=self.model,action=self.model_action,**arguments)
        if self.format_template:
            try:
                self.output             = await self.template_render(self.format_template,strict=True,
                    message             = message,
                    messages            = messages,
                    parameters          = arguments,
                )
            except BaseException as e:
                self.output             = f'Model调用异常: ```\n{str(e)}\n{traceback.format_exc()}\n```'
        return self.output

    def toFunction(self):
        return {
            "type"                      : "function",
                "function"              : {
                    "name"              : self.name,
                    "description"       : self.description,
                    "parameters"        : self.model_params.toJSON()
                }
            }
