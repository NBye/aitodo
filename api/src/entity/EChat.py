from __future__ import annotations
import importlib,time,os,json,re,traceback
import asyncio
from typing import List, Dict

from src.super.ESModel import ESModel
from src.entity.EChatMessage import EChatMessage
from src.entity.EUser import EUser,EAtUser,EAssistant
from src.entity.EFile import EFile
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EUserAction import EUserAction
from src.entity.EUserActionAgent import Agent
from src.utils.funcs import log

import config
from src.utils.Datetime import Datetime
from src.utils.errors import CodeError
from src.utils.AsyncIteratorQuque import AsyncIteratorQuque
from src.utils.Template import Template

class EChat(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        "user_ids"                      : [],
        "memories"                      : {},
        "metadata"                      : {},
        "temporary"                     : False,
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
                "organization_id"       : {"type": "keyword"},  # 组织ID
                "task_id"               : {"type": "keyword"},  # 组织ID
                "user_id"               : {"type": "keyword"},  # 创建者ID
                "user_ids"              : {"type": "keyword"},  # 相关用户
                "name"                  : {"type": "text"},
                "remark"                : {"type": "text"},
                "temporary"             : {"type": "boolean"},  # 临时聊天、接待客户的
                "avatar"                : {"type": "keyword","index":False},
                "memories"              : {"type": "object","enabled": False}, # 记忆，聊天室内所有AI以ID为key的，存储记忆数据
                "metadata"              : {"type": "object","enabled": False}, # 自定义数据
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    def __init__(self,**data):
        super().__init__(**data)

    async def _assistant_reply_refused (self,assistant:EUser)->EChatMessage|bool:
        # 已离开组织
        if not assistant.join_info:
            reply                           = await EChatMessage.create(
                virtual                     = True,
                chat_id                     = self._id,
                user_id                     = assistant._id,
                user_nickname               = assistant.nickname,
                user_avatar                 = assistant.avatar,
                user_gender                 = assistant.gender,
                role                        = 'assistant',
                status                      = 'completed',
                completed                   = Datetime.afrom().format(),
                content                     = '不好意思,我已经不在当前组织了。',
            )
            self.user_ids.remove(assistant._id)
            await self.upset(user_ids=self.user_ids)
            return reply
        # 组织内被禁言
        elif assistant.join_info.disabled:
            return True
        # 组织内雇佣过期
        elif assistant.join_info.expired and Datetime.afrom(assistant.join_info.expired) < Datetime.afrom():
            reply                           = await EChatMessage.create(
                # virtual                     = True,
                chat_id                     = self._id,
                user_id                     = assistant._id,
                user_nickname               = assistant.nickname,
                user_avatar                 = assistant.avatar,
                user_gender                 = assistant.gender,
                role                        = 'assistant',
                status                      = 'completed',
                completed                   = Datetime.afrom().format(),
                content                     = '工资都不给，我不干了！',
            )
            return reply
        else:
            return False

    async def _assistant_reply_messages(self,message:EChatMessage,assistant:EUser)->list[EChatMessage]:
        query                           = {"bool": {
            "must":[{'term':{'chat_id':self._id}},{'term':{'status':'completed'}},],
            "must_not":[{"term": {"_id": message._id }}],
        }}
        messages,count                  = await self.messages(
            size                        = assistant.settings.get('message_size',20),
            query                       = query,
            sort                        = [{"timestamp": "desc"}],
            _source                     = {"excludes": ["tools","understand","logs"]},
        )
        # 多AI互动式，非自己则认为是其他用户说的。
        for m in messages:
            m.role                      = 'assistant' if m.user_id==assistant._id else 'user'
        messages.reverse()
        return messages

    async def _assistant_reply_system(self,assistant:EUser,users:list[EUser])->EChatMessage:
        content                         = await Template(
            assistant.settings.get('definition') or config.TEMPLATE_DEFINITION,
            users                       = [await u.to_safe_dict() for u in users],
            assistant                   = await assistant.to_safe_dict(),
            user                   = await assistant.to_safe_dict(),
        )
        return await EChatMessage.create(virtual=True,content=content,role='system',status='completed')

    async def _assistant_reply_message(self,user):
        reply                           = await EChatMessage.create(
            chat_id                     = self._id,
            user_id                     = user._id,
            user_nickname               = user.nickname,
            user_avatar                 = user.avatar,
            user_gender                 = user.gender,
            tools                       = [],
            role                        = 'assistant',
            status                      = 'in_thought',
            status_description          = '正在思考您的问题...'
        )
        return reply

    async def _assistant_reply_at_users(self,content,users:list[EUser],assistant:EUser)->(list[EAtUser],list[EUser]):
        at_users_names                  = set(re.findall(r'@([\w\u4e00-\u9fa5]+)', content))
        at_users                        = []
        at_assistants                   = []
        for u in users:
            nickname                    = u.nickname
            aliasname                   = u.get('join_info',{}).get('aliasname','')
            if nickname in at_users_names or aliasname in at_users_names:
                if u._id == assistant._id:
                    continue
                if u.role=='assistant':
                    at_assistants.append(u)
                at_users.append(EAtUser(u)) 
        return at_users,at_assistants

    
    async def _assistant_reply_event(self,queue,message:EChatMessage,organization,assistant:EUser,users=[],must=False,depth=0):
        cache  = {}
        async for reply in self._assistant_reply(queue,message=message,organization=organization,assistant=assistant,users=users,must=must,depth=depth):
            _id                         = reply.get('_id')
            if _id in cache:
                data = {'_id':_id,'chat_id':reply.get('chat_id'),'content':reply.get('content','')}
                for k in '_id,status,status_description,content,completed,at_users,prompts,user_id,user_nickname,user_avatar,user_gender'.split(','):
                    if cache[_id][k]!= reply.get(k):
                        data[k]         = reply.get(k)
                cache[_id].update(data)
            else:
                data = {k:reply.get(k) for k in '_id,chat_id,user_id,user_nickname,user_avatar,user_gender,prompts,files,at_users,role,status,status_description,content,completed'.split(',')}
                cache[_id] = data
            yield data
            await organization.event_publish('chat-message-stream',data)
        await asyncio.sleep(0.1)


    async def _assistant_reply(self,queue,message:EChatMessage,organization,assistant:EUser,users=[],must=False,depth=0):
        # 1. 部分情况拒绝回复
        if reply := await self._assistant_reply_refused(assistant):
            if isinstance(reply, EChatMessage):
                yield {**reply}
            await asyncio.sleep(0.1)
            return
        try:
            # 2. 获取近几条上下文消息(不包含，最新用户消息)
            messages                    = await self._assistant_reply_messages(message,assistant)
            # 3. 聊天室增加 system
            messages.insert(0,await self._assistant_reply_system(assistant,users))
            # 4. 判断是否与我相关,无关不回复
            if must==False and await assistant.related_me(message,messages)==False:
                await asyncio.sleep(0.1)
                return
            # 5. 推送回复消息
            if reply := await self._assistant_reply_message(assistant):
                yield {**reply} 
            # 6. 意图识别 & 总结回复
            total_content               = ''    # 汇总返回内容
            async for buff in assistant.chat_reading(self,message,messages,reply):
                total_content           += buff
                yield {**reply,'content':buff}
            # 7. 获取@user，@ai
            at_users,at_assistants      = await self._assistant_reply_at_users(total_content,users,assistant)
            if at_users:
                await reply.upset(refresh=False,at_users=at_users,status='completed')
                yield {**reply,'content':''}
            # 8. @ai,直接回复
            if len(at_assistants) and depth < 5:
                reply['role']           = 'user'
                for u in at_assistants:
                    queue.join(self._assistant_reply_event(queue=queue,message=reply,organization=organization,assistant=u,users=users,must=True,depth=depth+1))
        except BaseException as e:
            if not reply:
                reply                   = await self._assistant_reply_message(assistant)
            await log(traceback.format_exc(),name='chat-reply.log')
            if isinstance(e,CodeError):
                content                 = f'{reply.content}\n\n{str(e)}'
            else:
                content                 = f'{reply.content}\n```\n{str(e)}\n{traceback.format_exc()}\n```'
            await reply.upset(
                content                 = content,
                status                  = 'incomplete',
                status_description      = '生成异常',
                completed               = Datetime.afrom().format()
            )
            yield {**reply}
        
    async def _send_users(self)->list[EUser]:
        users                           = await self.users(user_source=[
            'nickname','avatar','gender','role','settings','introduction','slogan','birthday','creator_organization_id',
        ])
        query                           = {
            "bool" : {"must":[
                {'terms':{'user_id':[item._id for item in users]}},
                {'term':{'enabled':True}},
            ]},
        }
        action_map                      = {}
        ea_list,_                       = await EUserAction.search(query=query,_source=['user_id','organization_id','name','description','agent_list','type','settings'])
        for action in ea_list: 
            if not action_map.get(action.user_id,None):
                action_map[action.user_id] = []
            action_map[action.user_id].append(action)
        for i,u in enumerate(users):
            users[i]['action_list']     = action_map.get(u['_id'],[])
        # print(json.dumps(users,indent=4, ensure_ascii=False))
        return users

    async def _send_at_users(self,at_users:list,users:list[EUser])->list[EAtUser]:
        user_map                        = {u._id:u for u in users}
        at_user_lis                     = []
        for u in at_users:
            if u['_id'] in user_map:
                u                       = user_map[u['_id']]
                at_user_lis.append(EAtUser(u))
        return at_user_lis

    async def _send_message(self,content,user,files,at_users):
        return await EChatMessage.create(
            chat_id                     = self._id,
            user_id                     = user._id,
            user_nickname               = user.nickname,
            user_avatar                 = user.avatar,
            user_gender                 = user.gender,
            files                       = files,
            at_users                    = at_users,
            role                        = 'user',
            status                      = 'completed',
            content                     = content,
            completed                   = Datetime.afrom().format("%Y-%m-%d %H:%M:%S"),
        )

    async def send(self,content :str,organization:EOrganization, user:EUser, files:List[EFile]=[],at_users:list=[]):
        # 1. 获取聊天室内用户以及相应的Agent
        users                           = await self._send_users()
        # 2. 校验at用户
        at_users                        = await self._send_at_users(at_users,users)
        if len(at_users)==0:
            _,at_users                  = await self._assistant_reply_at_users(content,users,user)
        at_user_ids                     = [u['_id'] for u in at_users]
        # 3. 构建发送者消息
        message                         = await self._send_message(content,user,files,at_users)
        yield message
        await organization.event_publish('chat-message-stream',message)
        # 4. 解析哪些人回复
        queue                           = AsyncIteratorQuque()
        for u in users:
            if u.role!='assistant':
                continue                # 不是AI员工不用回复
            elif at_user_ids and u._id not in at_user_ids:
                continue                # 指定用户，且不在指定列表 不回复
            elif u._id in at_user_ids:  # 在指定列表必须回复
                queue.join(self._assistant_reply_event(queue=queue,message=message,organization=organization,assistant=u,users=users,must=True))
            elif len(users) <= 2:       # 聊天室内只有2个人必须回复
                queue.join(self._assistant_reply_event(queue=queue,message=message,organization=organization,assistant=u,users=users,must=True))
            else:                       # 其他情况思考相关后在回复
                queue.join(self._assistant_reply_event(queue=queue,message=message,organization=organization,assistant=u,users=users,must=False))
        cache  = {}
        async for reply in queue.consume():
            # print(Datetime.afrom().format(), reply['status'],reply['content'],f"({reply['status_description']})")
            _id                         = reply.get('_id')
            if _id in cache:
                data = {'_id':_id,'chat_id':reply.get('chat_id'),'content':reply.get('content','')}
                for k in '_id,status,status_description,content,completed,at_users,prompts'.split(','):
                    if cache[_id][k]!= reply.get(k):
                        data[k]         = reply.get(k)
                cache[_id].update(data)
            else:
                data = {k:reply.get(k) for k in '_id,chat_id,user_id,user_nickname,user_avatar,user_gender,prompts,files,at_users,role,status,status_description,content,completed'.split(',')}
                cache[_id] = data
            yield data
            
    # 总结备注
    async def summary(self):
        query                           = {"bool": {
            "must":[{'term':{'chat_id':self._id}},{'term':{'status':'completed'}},]},
        }
        messages,count                  = await self.messages(
            size                        = 50,
            query                       = query,
            sort                        = [{"timestamp": "desc"}],
            _source                     = {"excludes": ["tools","understand"]},
        )
        if len(messages)<2:
            return ''
        messages.reverse()
        messages.append(await EChatMessage.create(virtual=True,content='以上帝视角: 对当前聊天整理一段20个字的摘要'))
        user                            = None
        for u in await self.users():
            if u.role != 'assistant':
                continue
            elif u['join_info']['disabled']:
                continue
            elif u['join_info']['expired'] and Datetime.afrom(u['join_info']['expired']) > Datetime.afrom():
                continue
            else:
                user                    = await EUser.afrom(_id=u._id)
                break
        if user == None:
            return ''
        options                         = {
            "temperature"               : 0.1,
            "num_ctx"                   : 4096,
            "stream"                    : False,
            "messages"                  : messages
        }
        async for data,_ in user.execute_model('Generate.generate',**options):
            await self.upset(remark=data['content'])
            return data['content']

    async def messages(self,**options)->(list[EChatMessage],int):
        messages,count                  = await EChatMessage.search(**options)
        return messages,count

    async def users(self,user_source=None,join_source=None):
        query                           = { 
            "bool"                      : {"must":[
                {"term": {"organization_id": self.organization_id}},
                {"terms": {"user_id": self.user_ids}},
            ]},
        }
        if user_source == None:
            user_source                 = ['nickname','avatar','gender','role']
        if join_source == None:
            join_source                 = ['aliasname','created','reception_status','disabled','disabled_reason','remark','user_id','expired']
        users,_                         = await EOrganizationUser.search(query=query,_source=join_source)
        join_info                       = {u.user_id:u for u in users}
        users,_                         = await EUser.search(query={"terms": {"_id": self.user_ids}},sort=[{'created':'asc'}],_source=user_source)
        for i,user in enumerate(users):
            users[i]                    = user.desensitization()
            users[i]['join_info']       = join_info.get(user._id,{})
        return users

    # 删除数据
    async def destroy(self,refresh=False):
        from src.entity.EFile import EFile
        if self.avatar:
            eFile                       = await EFile.afrom(url=self.avatar)
            if eFile:
                await eFile.destroy()
        await super().destroy(refresh=refresh)
        await EChatMessage.destroyMany(query={'term':{'chat_id':self._id}})
        return True