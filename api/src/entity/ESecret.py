from __future__ import annotations
import time,json,uuid
from typing import List, Dict

from datetime import datetime,timedelta

from src.super.ESModel import ESModel

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization

class ESecret(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        'enabled'                       : True,
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
                "organization_id"       : {"type": "keyword"},      # 所属组织ID  

                "description"           : {"type": "text"},         # 描述
                "key"                   : {"type": "keyword"},      # 密钥值

                "type"                  : {"type": "keyword"},      # 用途类型 api,

                "enabled"               : {"type": "boolean"},

                "expired"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,user:EUser,organization:EOrganization=None,refresh=True,virtual=False,expired=None,**attrs):
        if expired == None:
            now                         = datetime.now()
            later                       = now + timedelta(days=365*100)
            expired                     = later.strftime("%Y-%m-%d 00:00:00")
        attrs['key']                    = str(uuid.uuid4())
        attrs['user_id']                = user._id
        if organization:
            attrs['organization_id']    = organization._id
        return await super().create(refresh=refresh,virtual=virtual,expired=expired,**attrs)