import json
from datetime import datetime, timedelta, timezone

from quart import request
from src.entity.ECache import ECache
from src.entity.EUser import EUser
from src.entity.EChat import EChat
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.ESecret import ESecret

from src.utils.errors import CodeError

import config


def getToken():
    return request.headers.get('token') or request.cookies.get('token')

class BaseController:
    user                                = None
    organization                        = None

    VERIFY_LIST                         = []

    async def _generate(self,completion):
        async for message in completion:
            id                          = f'id: {message["id"]}\n' if message.get('id') else ''
            event                       = f'event: {message["event"]}\n' if message.get('event') else ''
            data                        = json.dumps(message['data']) if isinstance(message['data'],dict) else message['data']
            yield f"{event}{id}data: {data}\n\n"
            
    async def _async_init(self):
        pass

    def get_header(self,k=None,default=None):
        if k:
            return request.headers.get(k) or default
        else:
            return request.headers
            
    def get_cookie(self,k=None,default=None):
        if k:
            return request.cookies.get(k) or default
        else:
            return request.cookies

    async def get_files(self):
        files                           = await request.files
        return files

    async def get_post(self,k=None,default=None):
        if 'json' in request.headers.get('Content-Type'):
            post                        = await request.get_json()
        else:
            post                        = {key: value for key, value in (await request.form).items()}
        if k == None:
            return post
        data                            = post.get(k,None)
        if data=='' or data==None:
            data                        = default
        if data and k=='time_range':
            for i,time_str in enumerate(data):
                if 'T' in time_str:
                    utc_time            = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    shanghai_tz         = timezone(timedelta(hours=8))
                    local_time          = utc_time.replace(tzinfo=timezone.utc).astimezone(shanghai_tz)
                    data[i]             = local_time.strftime("%Y-%m-%d %H:%M:%S")
        return data

    async def _check_data(self,keys=None,verify_list=None):
        data                            = {}
        post                            = await self.get_post()
        if verify_list == None:
            verify_list                 = self.VERIFY_LIST
        for k,l,r,m in verify_list:
            v                           = post.get(k,None)
            if isinstance(v, str) and (len(v)>l[1] or len(v)<l[0]):
                raise CodeError(m)
            elif isinstance(v, str) and r and not re.match(r, v):
                raise CodeError(m)
            elif isinstance(v, dict) and len(json.dumps(v)) > l[1]:
                raise CodeError(m)
            elif keys!=None and k not in keys:
                continue
            elif v != None:
                data[k]                  = v
        return data
    
    async def splitSortList(self):
        post                            = await self.get_post()
        sort                            = post.get('sort','created desc')
        sort_list                       = []
        if sort:
            for item in sort.split(','):
                field, order = item.strip().split()
                sort_list.append({field: {'order':order}})
        return sort_list

class ClientController(BaseController):

    async def _async_init(self):
        token                           = getToken()
        if token == None:
            raise CodeError('未登录',401)
        token,user,session              = await EUser.login(type='0',token=token)
        self.token                      = token
        self.user                       = user
        self.session                    = session

        organization_id                 = request.args.get('organization_id',None) or self.session.get('organization_id',None)
        if organization_id:
            self.organization           = await EOrganization.afrom(_id=organization_id)
    
    async def getOrganization(self,organization_id):
        if self.organization and self.organization._id == organization_id:
            return self.organization
        else:
            return await EOrganization.afrom(_id=organization_id)
            
    async def getUser(self,user_id)->EUser:
        if self.user and self.user._id == user_id:
            return self.user
        else:
            return await EUser.afrom(_id=user_id)

class OrganizationController(ClientController):

    async def _async_init(self):
        await super()._async_init()
        if not self.organization:
            raise CodeError('无效的组织',405)
        self.organization_user          = await EOrganizationUser.afrom(organization_id=self.organization._id,user_id=self.user._id)
        if not self.organization_user:
            raise CodeError('当前组织您没有权限',405)
        if self.organization_user.disabled:
            raise CodeError(self.organization_user.disabled_reason or '当前组织对您封禁',405)
            
    async def _get_organization(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        if organization_id:
            organization                = await EOrganization.afrom(_id=organization_id)
        else:
            organization                = self.organization
        if not organization or organization.user_id != self.user._id:
            raise CodeError('组织创建者有权访问',403)
        return organization
            
class OpenController(BaseController):

    async def _async_init(self):
        await super()._async_init()
        auth_header                     = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key                     = auth_header[len('Bearer '):]
        else:
            api_key                     = request.headers.get('api_key') or request.cookies.get('api_key')
        if api_key == None:
            raise CodeError('无权限01',401)
        secret                          = await ESecret.afrom(key=api_key)
        if secret==None:
            raise CodeError('无权限02',401)
        organization                    = await EOrganization.afrom(_id=secret.organization_id)
        if organization==None:
            raise CodeError('无权限03',401)
        user                            = await EUser.afrom(_id=secret.user_id)
        if user==None:
            raise CodeError('无权限04',401)
        self.organization               = organization
        self.user                       = user

class ContableController(BaseController):

    async def _async_init(self):
        await super()._async_init()
        if not config.ALLOWED_IP:
            return 
        forwarded_for                   = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            real_ip = forwarded_for.split(',')[0]
        else:
            real_ip = request.remote_addr
        if real_ip not in config.ALLOWED_IP:
            raise CodeError('无权限05',401)
        print('real_ip:',real_ip)

class PluginController(BaseController):
    
    def __init__(self,**data):
        super().__init__(**data)
        self.user                           = None
        self.chat                           = None
        self.organization                   = None
        self.assistant                      = None

    async def current_user(self):
        if not self.user:
            user_id                         = request.headers.get('user-id')
            self.user                       = await EUser.afrom(_id=user_id)
        return self.user

    async def current_chat(self):
        if not self.chat:
            chat_id                         = request.headers.get('chat-id')
            self.chat                       = await EChat.afrom(_id=chat_id)
        return self.chat

    async def current_organization(self):
        if not self.organization:
            organization_id                 = request.headers.get('organization-id')
            self.organization               = await EOrganization.afrom(_id=organization_id)
        return self.organization

    async def current_assistant(self):
        if not self.assistant:
            assistant_id                    = request.headers.get('assistant-id')
            self.assistant                  = await EUser.afrom(_id=assistant_id)
        return self.assistant