import time,json,re
from typing import List, Dict
from datetime import datetime

from src.utils.U62Id import U62Id
from src.utils.CDict import CDict

from src.entity.EChatMessage import EChatMessage
from src.entity.EUserActionAgent import Agent
from src.entity.EFile import EFile

import mammoth

class AgentDocx(Agent):
    def __init__(self, file_id,**data):
        super().__init__(**data)
        self.name                       = data.get("name","docx")
        self.description                = f'解析{self.name}'

        self.file_id                    = file_id
        self.content                    = ''

    async def execute(self,message:EChatMessage=None,messages:list[EChatMessage]=[],arguments={}):
        tokens_total                    = 0
        prompt_tokens_total             = 0
        text                            = ''
        efile                           = await EFile.afrom(_id=self.file_id,_must=True)
        with open(efile.get_path(), "rb") as docx:
            result                      = mammoth.convert(docx)
            text                        = re.sub(r'base64,[^"]+', '', result.value) # 目的是有的里边带有图片，导致太大超出大模型的上下长度
        self.output                     =  f'文件: {efile["name"]}\n'
        self.output                     += f'1. 文件ID: {efile["_id"]}\n'
        self.output                     += f'4. 文件格式: {efile["type"]}\n'
        self.output                     += f'3. 文件大小: {efile["size"]}bit\n'
        self.output                     += f'2. 网络地址: {await efile.http_url()}\n'
        self.output                     += f'5. 文件内容:\n{text}'
        self.content                    = text
        return self.output
