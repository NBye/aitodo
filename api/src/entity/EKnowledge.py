from __future__ import annotations
from src.super.ESModel import ESModel
from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser

from src.utils.U62Id import U62Id

class EKnowledge(ESModel):

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
                "user_id"               : {"type": "keyword"}, 
                "organization_id"       : {"type": "keyword"}, 
                "knowledge_bucket_id"   : {"type": "keyword"}, 
                "file_id"               : {"type": "keyword"},  #是否关联某个文件

                "batch"                 : {"type": "keyword"},  # 批次号
                "serial"                : {"type": "integer"},
                
                "text"                  : {"type": "text"},     #知识正文

                "query_vector"          : {"type": "dense_vector", "dims": 1024,"similarity": "cosine",}, # 余弦相似cosine|点积dot_product
                "query_tokens"          : {"type": "integer"},

                "enabled"               : {"type": "boolean"},  #知识启用禁用
                "size"                  : {"type": "integer"},  #知识的存储大小

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def vector_embedding(cls,vector,knowledge_bucket_id,size=3):
        query                       = {
            "bool" : {
                "filter":[
                    {"term": {"knowledge_bucket_id": knowledge_bucket_id}},
                ],
                "must":[
                    {"knn":{
                        "field"                     :"query_vector",
                        "query_vector"              : vector,
                        "num_candidates"            : 10000
                    }}
                ]
            },
        }
        list,total                      = await EKnowledge.search(query=query,size=size,track_total_hits=10000,_source={'excludes':['query_vector']})
        return '\n'.join([item.text for item in list])

