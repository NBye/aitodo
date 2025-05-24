from __future__ import annotations
import time

from src.super.ESModel import ESModel
from datetime import datetime, timedelta

import config

class ELog(ESModel):
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
                "index"                 : {"type": "keyword"},
                "description"           : {"type": "text"},
                "content"               : {"type": "text"},

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "timestamp"             : {"type": "date","format": "epoch_millis"},
            }
        }
    }
