from __future__ import annotations
from src.super.ESModel import ESModel
from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser

import config

class EKnowledgeBucket(ESModel):

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
                
                "name"                  : {"type": "text"},     # 知识分组名称
                "description"           : {"type": "text"},     # 知识分组描述

                "query_vector"          : {"type": "dense_vector", "dims": 1024,"similarity": "cosine",}, # 余弦相似cosine|点积dot_product
                "query_tokens"          : {"type": "integer"},
                
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }
