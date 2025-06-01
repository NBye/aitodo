from __future__ import annotations
import time,json,uuid,asyncio
from typing import List, Dict

from datetime import datetime,timedelta

from src.super.ESModel import ESModel,connetES

from src.entity.EUser import EUser,EAtUser
from src.entity.EChat import EChat
from src.entity.EOrganization import EOrganization

class ETask(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        'executor_user_role'            : 'assistant',
        'enabled'                       : True,

        'status'                        : 'pending',

        'cron_enabled'                  : False,
        'cron_expr'                     : "* * * * *",

        'recurrence_rule'               : '',

        'success'                       : 0,
        'failure'                       : 0,
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
                "organization_id"       : {"type": "keyword"},      # 所属组织ID  
                "user_id"               : {"type": "keyword"},      # 发布任务用户ID
                "executor_user_id"      : {"type": "keyword"},      # 执行任务用户ID
                "executor_user_role"    : {"type": "keyword"},      # 执行任务用户角色
                
                "status"                : {"type": "keyword"},      # 状态，pending|running|completed|failed
                "status_description"    : {"type": "text"},         # 
                
                "title"                 : {"type": "text"},         # 任务标题
                "description"           : {"type": "text"},         # 描述
                "enabled"               : {"type": "boolean"},
                "success"               : {"type": "integer"},      # 成功次数
                "failure"               : {"type": "integer"},      # 失败次数

                "cron_enabled"          : {"type": "boolean"},
                "cron_expr"             : {"type": "keyword"},      # 周期设置
                
                "schedule_time"         : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"},  # 定时执行时间，立即执行就是当前时间
                
                "consumer_id"           : {"type": "keyword"},
                "consumer_ts"           : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,user:EUser,executor:EUser,organization:EOrganization,refresh=True,virtual=False,**attrs):
        attrs['user_id']                = user._id
        attrs['organization_id']        = organization._id
        attrs['executor_user_id']       = executor._id
        attrs['executor_user_role']     = executor.role
        if not attrs.get('schedule_time',None):
            attrs['schedule_time']      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(attrs)
        task                            = await super().create(refresh=refresh,virtual=virtual,**attrs)
        task['executor']                = executor
        await organization.event_publish('task-create',{"task":task})
        return task


    @classmethod
    async def fetch(cls,consumer_id):
        while True:
            current_time                = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            es,indexname                = await connetES(cls)
            script                      = {
                "source": """
                    if (ctx._source.status == 'pending') {
                        ctx._source.status = 'running';
                        ctx._source.consumer_id = params.consumer_id;
                        ctx._source.consumer_ts = params.consumer_ts;
                    } else {
                        ctx.op = 'noop';
                    }
                """,
                "lang"                  : "painless",
                "params"                : {
                    "consumer_id"       : consumer_id,
                    "consumer_ts"       : current_time
                }
            }
            body                        = {
                "size"                  : 1,
                "sort"                  : [{"schedule_time": "asc"}],
                "query"                 : {"term": {"status": "pending"}},
                "query"                 : {
                    "bool"              : {
                        "must"          : [
                            {"term"     : {"status": "pending"}},
                            {"range"    : {"schedule_time": {"lte": current_time}}}
                        ]
                    }
                },
                "script"                : script,
                "conflicts"             : "proceed"
            }
            result                      = await es.update_by_query(index=indexname, body=body, refresh=True)
            print(current_time)
            print(result)
            if result.get("updated", 0)==0:
                yield None
                await asyncio.sleep(0.1)
            else:
                search_body             = {
                    "size"              : 1,
                    "sort"              : [{"schedule_time": "asc"}],
                    "query"             : {
                        "bool"          : {
                            "must"      : [
                                {"term" : {"status": "running"}},
                                {"term" : {"consumer_id": consumer_id}}
                            ]
                        }
                    }
                }
                doc                     = await es.search(index=indexname, body=search_body)
                hits                    = doc.get("hits", {}).get("hits", [])
                if hits:
                    for data in hits:
                        yield cls(_id=data['_id'],**data['_source'])
                else:
                    yield None
                    await asyncio.sleep(0.1)

    async def consumer(self,consumer_id):
        user                            = await EUser.afrom(_id=self.user_id)
        executor                        = await EUser.afrom(_id=self.executor_user_id)
        organization                    = await EOrganization.afrom(_id=self.organization_id)
        data                            = {
            'name'                      : self.title,
            'remark'                    : self.description,
            'avatar'                    : executor.avatar,
            'user_id'                   : self.executor_user_id,
            'organization_id'           : self.organization_id,
            'task_id'                   : self._id,
            'user_ids'                  : [self.executor_user_id,self.user_id]
        }
        chat                            = await EChat.create(refresh=True,**data)
        completion                      = chat.send(
            content                     = self.description,
            organization                = organization,
            user                        = user,
            files                       = [],
            at_users                    = [EAtUser(executor)],
        )
        async for message in completion:
            # print(message['content'],end='')
            pass