from __future__ import annotations
from src.super.ESModel import ESModel
import config
from src.utils.Datetime import Datetime
from src.utils.Template import Template
import time,json
from datetime import datetime
from src.utils.funcs import text_indent


class EChatMessage(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score','tools']
    DEFAULT_ATTRVALUES                  = {
       "role"                           : 'user',
       "status"                         : 'in_progress',
       "status_description"             : '',
       "embeddings"                     : [],
       "tools"                          : {},
       "at_users"                       : [],
       "files"                          : [],
       "tokens"                         : 0,
       "completed"                      : None,
       "understand"                     : '',
       "content_command"                : [],
       "prompts"                        : [],
       "logs"                           : [],
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
                "chat_id"               : {"type": "keyword"},
                "user_id"               : {"type": "keyword"},                  # 相关方ID
                "user_nickname"         : {"type": "keyword"},                  # 相关方ID
                "user_avatar"           : {"type": "keyword"},                  # 相关方ID
                "user_gender"           : {"type": "keyword"},                  # 相关方
                "at_users"              : {"type": "object","enabled": False}, #@用户列表
                "files"                 : {"type": "object","enabled": False}, #相关文件
                
                "role"                  : {"type": "keyword"},
                "status"                : {"type": "keyword"},                  #'in_thought' 'in_progress','call_tools','incomplete','completed'
                "status_description"    : {"type": "text"},                     # 状态描述
                "understand"            : {"type": "text"},                     # 对问题的理解
                "content"               : {"type": "text"},                     # 输出的内容文本
                "content_command"       : {"type": "object","enabled": False},  # 输出的指令
                "embeddings"            : {"type": "object","enabled": False},
                "prompts"               : {"type": "object","enabled": False},  # 当前回复的推荐问题 ['prompt','prompts] 结构
                "tools"                 : {"type": "object","enabled": False},
                "model"                 : {"type": "keyword"},
                "tokens"                : {"type": "integer"},
                "logs"                  : {"type": "object","enabled": False},
                "completed"             : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "timestamp"             : {"type": "date","format": "epoch_millis"},
            }
        }
    }

    @classmethod
    async def create(cls,**data):
        data['timestamp']               = int(time.time() * 1000)
        return await super().create(**data)
    
    @classmethod
    async def transform_history(cls,user,messages=[]):
        text                            = "# 聊天记录:"
        coun                            = 0
        for i,m in enumerate(messages):
            utext,stext                 = await m.embedded(user)
            if stext:
                text                    +=f'\n\n<line><b>system</b></line>\n\n'
                text                    += stext
            text                        +=f'\n\n<line><b>{m.role}</b></line>\n\n'
            text                        += utext
            files                        = []
            for f in m.files:
                if f.is_image():
                    files.append(f'![{f.remark or f.name}]({config.HOST}{f.url}?w=200)')
                else:
                    files.append(f'[{f.remark or f.name}]({config.HOST}{f.url})')
            if len(files)>0:
                text                    += '\n\n'
                text                    += '\n\n'.join(files)
        return text

    @classmethod
    def contain_image(cls,messages=[]):
        for m in messages:
            for f in m.get('files',[]):
                if f.is_image():
                    return True
        return False

    async def copy(self,**data):
        return await EChatMessage.create(virtual=True,**{**self,**data})

    async def to_safe_dict(self):
        return dict(
            at_users                    = self.at_users,
            files                       = [await f.to_safe_dict() for f in self.files],
            content                     = self.content,
            content_command             = self.content_command,
            embeddings                  = self.embeddings,
            user                        = {
                '_id'                   : self.user_id,
                'role'                  : self.role,
                'avatar'                : self.user_avatar,
                'gender'                : self.user_gender,
                'nickname'              : self.user_nickname,
            },
        )

    async def embedded(self,user):
        utext                       = self.content
        stext                       = await Template(
            user.settings.get('template_embeddings') or config.TEMPLATE_EMBEDDINGS,
            ** await self.to_safe_dict()
        )
        return utext,stext

    async def log(self,list,remark='',**other):
        logs                            = [
            {"remark":remark,"list":list,"time":other['time'] if other.get('time',None) else int(time.time() * 1000)},
            *self.get('logs',[])
        ]
        await self.upset(logs=logs)

    def _deep_property(self):
        from src.entity.EFile import EFile
        for i,data in enumerate(self.files):
            self.files[i]               = EFile(**data)
