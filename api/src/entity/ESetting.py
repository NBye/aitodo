from __future__ import annotations
import time,json,uuid
from typing import List, Dict

from datetime import datetime,timedelta

from src.super.ESModel import ESModel

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization

class ESetting(ESModel):
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
                "organization_id"       : {"type": "keyword"},
                "user_id"               : {"type": "keyword"},

                "data"                  : {"type": "object","enabled": False},

                "enabled"               : {"type": "boolean"},

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,refresh=True,virtual=False,organization:EOrganization=None,user:EUser=None,**attrs):
        if organization:
            attrs['organization_id']        = organization._id
        if user:
            attrs['user_id']                = user._id
        return await super().create(refresh=refresh,virtual=virtual,**attrs)