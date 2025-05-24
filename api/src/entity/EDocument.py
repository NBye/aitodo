from __future__ import annotations
from src.super.ESModel import ESModel

class EDocument(ESModel):

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
                "title"                 : {"type": "text"},     # 标题
                "abstract"              : {"type": "text"},     # 摘要
                "text"                  : {"type": "text"},     # markdown 格式 支持前端 模板引擎
                "enabled"               : {"type": "boolean"},  # 禁用状态
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }
