from __future__ import annotations
import time,json

from src.super.ESModel import ESModel
from src.utils.errors import CodeError
from datetime import datetime, timedelta

import config

class EDataBase(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        
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
                "organization_id"       : {"type": "keyword"}, 
                "user_id"               : {"type": "keyword"}, 

                "type"                  : {"type": "keyword"},      # voice_clone | 

                "remark"                : {"type": "text"},         # 备注
                "content"               : {"type": "text"},         # json 字符串

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,organization=None,user=None,**data):
        content                         = data.get('content',None) or {}
        if not isinstance(content, str):
            data['content']             = json.dumps(content, ensure_ascii=False)
        if len(data.get('content'))>1000:
            raise CodeError('单条数据不得超过1000字符')
        if organization:
            data['organization_id']     = organization._id
        if user:
            data['user_id']             = user._id
        return await super().create(**data)


    
    async def upset(self,**data):
        content                         = data.get('content',None)
        if content!=None:
            if not isinstance(content, str):
                data['content']             = json.dumps(content, ensure_ascii=False)
            if len(data.get('content'))>1000:
                raise CodeError('单条数据不得超过1000字符')
        return await super().upset(**data)