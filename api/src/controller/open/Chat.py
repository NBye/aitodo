import json,sys
import config

from quart import request,Response

from src.super.controllers import OpenController

from src.entity.EChat import EChat
from src.entity.EChatMessage import EChatMessage
from src.entity.EUser import EUser
from src.entity.EFile import EFile
from src.entity.EOrganizationUser import EOrganizationUser

from src.utils.errors import CodeError 
from src.utils.Datetime import Datetime


async def generate(completion):
    async for message in completion:
        yield f"data: {json.dumps(message)}\n\n"

class Chat(OpenController):
    
    MAX_USER_NUMBER                     = 10

    async def create(self):
        post                            = await self.get_post()
        name                            = post.get('name','')
        user_ids                        = [self.user._id] + post.get('user_ids',[])
        if len(user_ids) > self.MAX_USER_NUMBER:
            raise CodeError(f'暂不支持超过{self.MAX_USER_NUMBER}人的聊天室')
        users,_                         = await EUser.search(query={"terms": {"_id": user_ids}},_source=['nickname','avatar'])
        if not name:
            name                        = (','.join(item['nickname'] for item in users[:4]))
        # 合并用户头像作为两天头像
        efile                           = None
        urls                            = []
        for item in users:
            if item['avatar']:
                urls.append(item['avatar'])
        if len(urls)>0:
            efile                       = await EFile.mergeImage(urls=urls, user=self.user,organization=self.organization,remark="多人聊天图标")
            avatar                      = efile.url
        else:
            avatar                      = ''
        data                            = {
            'name'                      : name,
            'avatar'                    : avatar,
            'user_id'                   : self.user._id,
            'organization_id'           : self.organization._id if self.organization else '',
            'user_ids'                  : user_ids
        }
        chat                            = await EChat.create(refresh=True,**data)
        if efile :
            await efile.upset(remark=f"聊天室{chat._id}图标")
        return {'chat':chat},

    async def info(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id',None)
        chat                            = await EChat.afrom(_id=chat_id)
        if chat == None:
            raise CodeError('找不到该聊天室')
        users                           = await chat.users()
        return {'chat':chat,'users':users},

    async def upset(self):
        post                            = await self.get_post()
        data                            = {}
        name                            = post.get('name',None)
        remark                          = post.get('remark',None)
        _id                             = post.get('chat_id')
        if not _id:
            raise CodeError('缺少参数')
        if len(name)>20:
            raise CodeError('名称不得超过20个字')
        if len(remark)>20:
            raise CodeError('备注不得超过50个字')
        if name:
            data['name']                = name
        if remark:
            data['remark']              = remark
        if not data:
            raise CodeError('请设置修改内容')
        chat                            = await EChat.afrom(_id=_id)
        if chat == None:
            raise CodeError('找不到该聊天室')
        if chat.user_id!=self.user._id:
            raise CodeError('无权限删除',403)
        await chat.upset(**data)
        return {'chat':chat},'修改成功'

    async def search(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','') # 组织相关的
        user_id                         = post.get('user_id','')         # 创建者id
        keyword                         = post.get('keyword','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',50))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[
                {"term": {"user_ids": self.user._id}}  # 相关的
            ]},
        }
        if organization_id:
            query["bool"]["must"].append({"term": {"organization_id": organization_id}})
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"remark": keyword}},
                        {"match": {"name"  : keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
        liss,count                      = await EChat.search(
            query                       = query,
            track_total_hits            = True,
            size                        = 50,
            sort                        = sort_list,
            _source                     = {'excludes':['user_ids','memories']}
        )
        for i,item in enumerate(liss):
            liss[i]                     = item.desensitization()
        return {"list":liss,'count':count},

    async def destroy(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id','')
        chat                            = await EChat.afrom(_id=chat_id)
        if chat == None:
            raise CodeError('找不到该聊天室')
        if chat.organization_id != self.organization._id:
            raise CodeError('无权限删除',403)
        await chat.destroy(refresh=True)
        await EChatMessage.destroyMany(query={'term':{'chat_id':chat_id}})
        return {},'删除成功'

    async def leave(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id','')
        chat                            = await EChat.afrom(_id=chat_id)
        if chat == None:
            raise CodeError('找不到该聊天室')
        user_id                         = post.get('user_id')
        user_ids                        = list(set(chat.user_ids))
        if user_id in user_ids:
            user_ids.remove(user_id)
        user                            = await EUser.afrom(_id=user_id)
        await chat.upset(user_ids=user_ids)
        # 更新头像
        slist,_                         = await EUser.search(query={"terms": {"_id": user_ids}},size=9,sort=[{'created':'asc'}],_source=['nickname','avatar'])
        if len(slist)>=2:
            urls                        = [item['avatar'] for item in slist]
            ofile                       = await EFile.mergeImage(urls=urls, user=self.user,organization=self.organization,remark=f"聊天室{chat._id}图标")
            if chat.avatar:
                efile                   = await EFile.afrom(url=chat.avatar)
                if efile:
                    await efile.destroy()
            await chat.upset(avatar=ofile.url)
        return {'chat':chat,'user':user.desensitization()},'移除成功'

    async def invite(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id','')
        chat                            = await EChat.afrom(_id=chat_id)
        if chat == None:
            raise CodeError('找不到该聊天室')
        user_ids                        = post.get('user_ids',[])
        if not user_ids or not isinstance(user_ids, list):
            raise CodeError('请传入正确的用户ID')
        query                           = {
            "bool"                      : {"must":[
                {"term": {"organization_id": chat.organization_id}},
                {"terms": {"user_id": user_ids}},
            ]},
        }
        users,_                         = await EOrganizationUser.search(query=query,_source="aliasname,created,reception_status,disabled,disabled_reason,remark,user_id".split(','))
        if len(user_ids) != len(users):
            raise CodeError('只能邀请本组织内的成员')
        if len(user_ids + chat.user_ids) > self.MAX_USER_NUMBER:
            raise CodeError(f'暂不支持超过{self.MAX_USER_NUMBER}人的聊天室')
        join_info                       = {}
        for u in users:
            join_info[u.user_id]        = u
        users,_                         = await EUser.search(query={"terms": {"_id": user_ids}},_source=['nickname','avatar','gender','role'])
        for i,user in enumerate(users):
            users[i]                    = user.desensitization()
            users[i]['join_info']       = join_info.get(user._id,None)
            if user._id not in chat.user_ids:
                chat.user_ids.append(user._id)
        await chat.upset(user_ids=chat.user_ids)
        if len(chat.user_ids)-len(user_ids) < 9:
            slist,_                     = await EUser.search(query={"terms": {"_id": chat.user_ids}},size=9,sort=[{'created':'asc'}],_source=['nickname','avatar'])
            urls                        = [item['avatar'] for item in slist]
            ofile                       = await EFile.mergeImage(urls=urls, user=self.user,organization=self.organization,remark=f"聊天室{chat._id}图标")
            if chat.avatar:
                efile                   = await EFile.afrom(url=chat.avatar)
                if efile:
                    await efile.destroy()
            await chat.upset(avatar=ofile.url)
        return {'chat':chat,'users':users},'加入成功'

    async def send(self,chat_id=''):
        post                            = await self.get_post()
        content                         = post.get('content','').strip()
        files                           = post.get('files',[])
        at_users                        = post.get('at_users',[])
        if not chat_id:
            chat_id                     = post.get('chat_id','').strip()
        if not content:
            raise CodeError('请输入问题内容。')
        if not chat_id:
            raise CodeError('缺少参数：chat_id')
        chat                            = await EChat.afrom(_id=chat_id)
        if chat==None:
            raise CodeError('当前会话丢失，请从新发起会话！')
        completion                      = chat.send(
            content,
            organization                = self.organization,
            user                        = self.user,
            files                       = [EFile(**f) for f in files],
            at_users                    = at_users
        )
        return Response(generate(completion), mimetype='text/event-stream')

    async def completion(self,assistant_id,platform=''):
        post                            = await self.get_post()
        model                           = post.get('model','')
        messages                        = post.get('post',[])
        tools                           = post.get('tools',[])
        stream                          = post.get('stream',True)
        temperature                     = post.get('temperature',True)
        
        assistant                       = await EUser.afrom(_id=assistant_id)
        if not assistant or assistant.role!='':
            raise CodeError('小秘书id不正确')
        organization                    = await EOrganization.afrom(_id=assistant.creator_organization_id)
        if platform=='bailian':
            from src.utils.model.bailian.Chat import send
        elif platform=='ollama':
            from src.utils.model.ollama.Chat import send
        elif platform=='other':
            from src.utils.model.other.Chat import send
        elif platform=='ragflow':
            from src.utils.model.ragflow.Chat import send
        else:
            raise Exception("未指定平台")
        completion                          = await send(model=model,messages=messages,organization=organization,user=assistant,tools=tools, stream=stream,temperature=temperature)
        return Response(generate(completion), mimetype='text/event-stream')
    
    async def messages(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id','')
        timestamp_lt                    = post.get('timestamp_lt',0)
        size                            = post.get('size',50)
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[
                {"term": {"chat_id": chat_id}}
            ]},
        }
        if timestamp_lt:
            query['bool']['must'].append({
                "range": {
                    "timestamp": {
                        "lt": int(timestamp_lt)
                    }
                }
            })
        list,count                      = await EChatMessage.search(
            size                        = size,
            track_total_hits            = True,
            query                       = query,
            sort                        = sort_list,
            _source                     = {"excludes": ["embeddings","tools","understand",'logs']},
        )
        for i,message in enumerate(list):
            list[i]                     = message.desensitization()

        return {"list":list,'count':count},


    async def messageInfo(self):
        post                            = await self.get_post()
        message_id                      = post.get('message_id','')
        if not message_id:
            raise CodeError('请传入消息ID')
        message                         = await EChatMessage.afrom(_id=message_id)
        return {'message':message},


    async def messageDel(self):
        post                            = await self.get_post()
        message_id                      = post.get('message_id','')
        if not message_id:
            raise CodeError('请传入消息ID')
        message                         = await EChatMessage.afrom(_id=message_id)
        if message:
            await message.destroy()
        return {},'删除成功'
