from quart import request,Response
from src.super.controllers import BaseController

from src.entity.EUser import EUser
from src.entity.EFile import EFile
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EChat import EChat
from src.entity.EChatMessage import EChatMessage

from src.utils.errors import CodeError
import json,traceback

async def generate(completion):
    async for message in completion:
        yield json.dumps(message, ensure_ascii=False)+"\n"
        
async def get_user():
    try:
        token                           = request.headers.get('token') or request.cookies.get('token')
        if token:
            token,user,session          = await EUser.login(type='0',token=token)
            return user
    except:
        pass
    user                                = await EUser.create(
        virtual                         = True,
        avatar                          = '',
        nickname                        = '游客',
        role                            = 'user',
    )
    user._id                            = ''
    return user

class Reception(BaseController):

    async def chat(self):
        post                            = await self.get_post()
        organization_assistant_id       = post.get('organization_assistant_id','')
        ou                              = await EOrganizationUser.afrom(_id=organization_assistant_id)
        if not ou or not ou.reception_status or ou.disabled:
            raise CodeError(f'接待专员不在线')
        chat                            = None
        user                            = await get_user()
        assistant                       = await EUser.afrom(_id=ou.user_id)
        if not assistant or assistant.role!='assistant':
            raise CodeError(f'接待专员已下线')
        if chat_id:=post.get('chat_id',''):
            chat                        = await EChat.afrom(_id=chat_id)
        if not chat:
            data                        = {
                'name'                  : f"{assistant.nickname}",
                'temporary'             : True,
                'avatar'                : '',
                'user_id'               : user._id,
                'user_ids'              : [assistant._id],
                'organization_id'       : ou.organization_id,
            }
            chat                        = await EChat.create(refresh=True,**data)
            await assistant.opening_answer(chat)
            await EChatMessage.refreshIndex()
        elif not chat.temporary:
            raise CodeError(f'无权限查看')
        elif assistant._id not in chat.user_ids:
            raise CodeError(f'无权限查看')
        return {'assistant':assistant,'user':user,'chat':chat},

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

    async def send(self):
        post                            = await self.get_post()
        chat_id                         = post.get('chat_id','')
        content                         = post.get('content','').strip()
        files                           = post.get('files',[])
        at_users                        = post.get('at_users',[])

        if content=='':
            raise CodeError('请输入问题内容。')
        if chat_id=='':
            raise CodeError('缺少参数：chat_id')
        chat                            = await EChat.afrom(_id=chat_id)
        if chat==None:
            raise CodeError('当前会话丢失，请从新发起会话！')
        ou                              = await EOrganizationUser.afrom(user_id=chat.user_ids[0],organization_id=chat.organization_id)
        if not ou or not ou.reception_status or ou.disabled:
            raise CodeError(f'接待专员不在线')
        organization                    = await EOrganization.afrom(_id=chat.organization_id)
        completion                      = chat.send(
            content,
            organization                = organization,
            user                        = await get_user(),
            files                       = [EFile(**f) for f in files],
            at_users                    = at_users
        )
        return Response(generate(completion), mimetype='text/event-stream',content_type='text/event-stream; charset=utf-8', )

    async def messageDel(self):
        post                            = await self.get_post()
        chat                            = (await self.chat())[0]['chat']
        message_id                      = post.get('message_id','')
        if not message_id:
            raise CodeError('请传入消息ID')
        message                         = await EChatMessage.afrom(_id=message_id)
        if message.chat_id != chat._id:
            raise CodeError('无权限删除消息')
        print(message)
        if message:
            await message.destroy()
        return {},'删除成功'

    async def messageInfo(self):
        post                            = await self.get_post()
        chat                            = (await self.chat())[0]['chat']
        message_id                      = post.get('message_id','')
        if not message_id:
            raise CodeError('请传入消息ID')
        message                         = await EChatMessage.afrom(_id=message_id)
        if message.chat_id != chat._id:
            raise CodeError('无权限删除消息')
        return {'message':message},

    
    async def metadata(self):
        chat                            = (await self.chat())[0]['chat']
        return {'metadata':chat.metadata or {}},

    async def metadata_save(self):
        chat                            = (await self.chat())[0]['chat']
        from src.entity.agent.tools import AgentMetadata
        post                            = await self.get_post()
        chat.metadata                   = post.get('metadata',None) or {}
        if not isinstance(chat.metadata, dict):
            chat.metadata               = {}
        AgentMetadata(chat).save()
        return {'metadata':chat.metadata},'保存成功'

    async def upload(self):
        chat_id                         = request.form.get('chat_id','')
        chat                            = await EChat.afrom(_id=chat_id)
        organization                    = await EOrganization.afrom(_id=chat.organization_id)
        user                            = await get_user()
        data                            = {}
        files                           = await request.files
        for k,fs in files.items():
            try:
                efile                   = await EFile.upload(fs, user, organization=organization, location='reception',refresh=False)
                data[k]                 = {**efile,**{'status':'success','reason': ''}}
            except BaseException as e:
                data[k]                 = {'status':'failed','reason': str(e),'stack':traceback.format_exc()} 
        return data,'上传成功'