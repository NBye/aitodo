import time,json
from typing import List, Dict
from datetime import datetime

from src.utils.U62Id import U62Id
from src.utils.CDict import CDict

from src.entity.EChatMessage import EChatMessage
from src.entity.EUserActionAgent import Agent
from src.entity.EKnowledge import EKnowledge

class AgentKnowledge(Agent):
    def __init__(self,knowledge_bucket_id:str,knowledge_bucket_name:str,**data):
        super().__init__(**data)
        self.knowledge_bucket_id        = knowledge_bucket_id
        self.knowledge_bucket_name      = knowledge_bucket_name

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        organization                    = await self.user.get_creator_organization()
        understand                      = await self.user.get_understand(message,messages)
        understand_vector,tokens        = await organization.text_to_vector(understand)
        self.output                     = await EKnowledge.vector_embedding(
            understand_vector,
            self.knowledge_bucket_id
        )         
        return self.output

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
