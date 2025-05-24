from quart import request,Response
from src.super.controllers import ClientController
import json
from openai import OpenAI

import httpx
from httpx import BasicAuth

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EFile import EFile
from src.entity.ECache import ECache

from src.utils.funcs import defOptimized,generateRole,async_exec
from src.utils.errors import CodeError
import config

class Organization(ClientController):

    VERIFY_LIST                         = [
        ('name',                [3,20],         None,       '组织名称3-20个字符以内'),
        ('slogan',              [0,200],        None,       '口号200个字符以内'),
        ('introduction',        [0,20000],      None,       '简介2万个字符以内'),
        ('settings',            [0,2000],       None,       ''),
    ]
    async def event(self):
        completion                      = self.organization.event_listen()
        return Response(self._generate(completion), mimetype='text/event-stream')

    async def create(self):
        data                            = await self._check_data(['name','slogan','introduction'])
        if not data.get('name',None):
            raise CodeError('组织名称必填')
        elif len(data['name']) < 3 or len(data['name'])>20:
            raise CodeError('组织名称3-20个字符以内')
        oz                              = await EOrganization.afrom(_source=['name'],**{'name.keyword':data['name']})
        if oz:
            raise CodeError('该名称已被使用')
        count                           = await EOrganization.count(query={'term':{'user_id':self.user._id}})
        if count >= 4:
            raise CodeError('一个账号最多可以创建4个组织')
        data['balance']                 = 0.0
        data['user_id']                 = self.user._id
        if data.get('slogan')=='':
            del data['slogan']
        organization                    = await EOrganization.create(refresh=True, user=self.user, **data)
        return {'organization':organization},

    async def createAssistant(self):
        count                           = await EOrganizationUser.count(query={'term':{'creator_organization_id':self.organization._id}})
        if count>=self.organization.settings["user_limit"]:
            raise CodeError(f'组织最多可以有个{self.organization.settings["user_limit"]}位成员')
        validation                      = [
                ('nickname',    [2,20],         None,       '昵称需要2~20个字符以内'),
                ('gender',      [2,2],          None,       '性别为 xx 或 xy'),
                ('slogan',      [0,200],        None,       '口号需要200个字符以内'),
                ('introduction',[0,20000],      None,       '简介不得超过两万个字符'),
                ('salary',      [0,20000],      None,       '收费信息包过大'),
                ('settings',    [0,20000],      None,       'AI设置数据过大'),
        ]
        data                            = await self._check_data(None,validation)
        nickname,gender,avatar          = generateRole()
        if not data.get('nickname',None):
            data['nickname']            = nickname
        if not data.get('avatar',None):
            data['avatar']              = avatar
        if not data.get('gender',None):
            data['gender']              = gender
        data['creator_organization_id'] = self.organization._id
        data['creator_user_id']         = self.user._id
        data['role']                    = 'assistant'
        data['public']                  = False

        for k in ['model','visionmodel','textmodel']:
            if not data['settings'][k]:
                raise CodeError('请完善大模型设置')

        assistant                       = await EUser.create(**data)
        ou                              = await self.organization.join(assistant,'一个有责任心的小秘书')
        user                            = assistant.desensitization()
        user['join_info']               = ou.desensitization()
        return {'user':user},'创建成功'    

    async def info(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id',None)
        ou                              = await EOrganizationUser.afrom(organization_id=organization_id,user_id=self.user._id)
        if not ou:
            raise CodeError('无权限查看',403)
        organization                    = await EOrganization.afrom(_id=organization_id,_must=True)
        if not organization:
            raise CodeError('组织不存在')
        user_count                      = await EOrganizationUser.count(query={'term':{'organization_id':organization._id}})
        aggs                            = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
            {"term": {"organization_id": organization._id}},
        ]}})
        storage_count                   = (aggs['total_size']['value'])/(1024**3)
        return {'organization':organization,'user_count':user_count,'storage_count':storage_count},

    async def upset(self):
        data                            = await self._check_data(['name','slogan','introduction','settings'])
        organization_id                 = await self.get_post('organization_id',None)
        if not organization_id:
            raise CodeError('未指定修改组织ID')
        organization                    = await EOrganization.afrom(_id=organization_id,_must=True)
        if organization.user_id != self.user._id:
            raise CodeError('只有创建者才可以修改',403)
        if data.get('name',None):
            if len(data['name']) < 3 or len(data['name'])>20:
                raise CodeError('组织名需要3-20个字符')
            oz                          = await EOrganization.afrom(_source=['name'],**{'name.keyword':data['name']})
            if oz and oz._id!=organization._id:
                raise CodeError('该名称已被使用')
        files                           = await request.files
        avatar                          = files.get('avatar')
        if avatar:
            remark                      = '组织“' + organization.name + '”的Logo'
            efile                       = await EFile.upload(avatar, self.user, organization=organization, location='public', remark=remark)
            data['avatar']              = efile.url
            if organization.avatar:
                oFile                   = await EFile.afrom(url=organization.avatar)
                if oFile:
                    await oFile.destroy()
                    
        await organization.upset(**data)
        return {'organization':organization},'保存成功'

    async def upavatar(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id')
        if not organization_id:
            return {},f'找不到数据',404
        organization                    = await EOrganization.afrom(organization_id)
        if not organization:
            return {},f'找不到数据{organization_id}',404
        if organization.user_id != self.user._id:
            return {},f'无权限修改',403
        files                           = await request.files
        avatar                          = files.get('avatar')
        if not avatar:
            return {},'请上传图片文件',0
        remark                          = '组织“' + organization.name + '”的Logo'
        efile                           = await EFile.upload(avatar, self.user, organization=organization, location='public',remark=remark)
        if organization.avatar:
            oFile                       = await EFile.afrom(url=organization.avatar)
            if oFile:
                await oFile.destroy()
        await organization.upset(avatar=efile.url)
        return {'avatar':efile.url},    

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        group                           = post.get('group','') #1我创建的，2我参与的 缺省2
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',50))
        sort_list                       = await self.splitSortList()
        joins                           = {}
        ou_list,_                       = await EOrganizationUser.search(query={'term':{'user_id':self.user._id}},_source=['organization_id','created','reception_status','disabled','disabled_reason','remark'])
        for ou in ou_list:
            joins[ou.organization_id]   = ou
        if not joins:
            return {'list':[],'total':0},
        query                           = {
            "bool"                      : {"must":[
                {'terms':{'_id':list(joins.keys())}}
            ]},
        }
        if group and str(group)=='1':
            query["bool"]["must"].append({'term':{'user_id':self.user._id}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"name": keyword}},
                        {"match": {"introduction": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        liss,total                      = await EOrganization.search(query=query,_source={"excludes": ["balance","introduction"]},sort=sort_list,track_total_hits=10000,**{'from':skip,'size':size})
        for i,organization in enumerate(liss):
            liss[i]                     = organization.desensitization()
            liss[i]['join_info']        = joins[organization._id].desensitization()
            del liss[i]['join_info']['organization_id']
        return {'list':liss,'total':total},

    async def invite(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        user_id                         = post.get('user_id','')
        if not organization_id or not user_id:
            raise CodeError('缺少参数')
        if await EOrganizationUser.afrom(organization_id=organization_id,user_id=user_id):
            raise CodeError('已加入该组织')
        organization                    = await EOrganization.afrom(_id=organization_id,_must=True)
        count                           = await EOrganizationUser.count(query={'term':{'creator_organization_id':organization._id}})
        if count>=organization.settings["user_limit"]:
            raise CodeError(f'组织最多可以有个{organization.settings["user_limit"]}位成员')
        user                            = await EUser.afrom(_id=user_id,_must=True)
        if user.role == 'assistant':
            salary                      = {'settlement':'auto',**post.get('salary',{})}
            salard                      = user.salary[salary['type']]
            if salary['price'] < 0:
                raise CodeError('薪酬数据错误')
            if not salard['enable']:
                raise CodeError('当前薪酬方式以关闭，请重试。')
            if float(salard['price'])!=float(salary['price']):
                raise CodeError('当前薪酬有所变化，请重试。',data={
                    'settle_salary' :salary['price'],
                    'settig_salary' :salard['price'],
                })
        else:
            salary                      = None
        await organization.join(user,f'由 {self.user.nickname} 邀请加入',salary=salary)
        return {'organization':organization},

    async def leave(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        user_id                         = post.get('user_id','')
        organization                    = await EOrganization.afrom(_id=organization_id)
        if not organization:
            raise CodeError('组织不存在')
        if user_id:
            user                        = await EUser.afrom(_id=user_id)
            if not user:
                raise CodeError('组织不存在')
        else:
            user                        = self.user
        await organization.leave(user)
        return {},'退出成功'

    async def switch(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        if not organization_id:
            raise CodeError('缺少参数')
        organization                    = await EOrganization.afrom(_id=organization_id,_must=True)
        await ECache.setData(self.token, 3600*24*7,refresh='true',
            user_id                     = self.user._id,
            organization_id             = organization._id
        )
        return {'organization':organization},f'成功进入该组织'

    async def destroy(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        if not organization_id:
            raise CodeError('缺少参数')
        organization                    = await EOrganization.afrom(_id=organization_id,_must=True)
        if organization.user_id != self.user._id:
            raise CodeError('只有组织的所有这才可删除')
        await organization.destroy()
        return {},'删除成功'

    async def recharge(self):
        organization_id                 = await self.get_post('organization_id')
        amount                          = await self.get_post('amount',200)
        if organization_id:
            organization                = await self.getOrganization(organization_id)
        else:
            organization                = self.organization
        data                            = await organization.recharge(self.user,float(amount))
        return data,

    async def settingInfo(self):
        organization                    = await self.getOrganization(await self.get_post('organization_id'))
        if organization.user_id != self.user._id:
            raise CodeError(f'无权限操作')
        return {'settings':organization.settings},
    
    async def settingSave(self):
        post                            = await self.get_post() 
        settings                        = {}
        allowed                         = [
            'bailian','ollama','nvidia','ragflow','other',
            'embedmodel',
            'join_code_enabled','join_code_value','join_invite_enabled',
        ]
        for k,v in post.get('settings',{}).items():
            if k in allowed:
                settings[k]             = v
        organization                    = await self.getOrganization(await self.get_post('organization_id'))
        if organization.user_id != self.user._id:
            raise CodeError(f'无权限操作')
        organization.settings.update(settings)
        await organization.upset(settings=organization.settings)
        return {'settings':settings},'保存成功'


    async def openai_models(self):
        post                            = await self.get_post()
        api_key                         = post.get('api_key') or ''
        base_url                        = post.get('base_url') or ''
        client                          = OpenAI(
            api_key                     = api_key,
            base_url                    = base_url,
        )
        models                          = []
        for m in await async_exec(client.models.list):
            if m.object == 'model':
                models.append({
                    'value'             : m.id,
                    'label'             : m.id,
                    'support'           : [],
                })
        return {'models':models},

    async def ollama_models(self):
        post                            = await self.get_post()
        host                            = post.get('host') or ''
        username                        = post.get('username') or ''
        password                        = post.get('password') or ''
        apikey                          = post.get('apikey') or ''
        headers                         = {}
        if username and password:
            auth                        = BasicAuth(username, password)
        elif apikey:
            headers["Authorization"]    = f"Bearer {apikey}"
        else:
            auth                        = None
        models                          = []
        async with httpx.AsyncClient() as client:
            response                    = await client.get(f'{host}/api/tags',headers=headers, auth=auth)
            if response.status_code != 200:
                raise CodeError(f'获取失败:http status:{response.status_code}')
            else:
                data                    = response.json()
                for m in data['models']:
                    models.append({
                        'value'         : m['name'],
                        'label'         : m['name'],
                        'support'       : [],
                    })
        return {'models':models},

    async def ragflow_models(self):
        models                          = [
            {
                'value'         : 'deepseek-chat',
                'label'         : 'deepseek-chat',
                'support'       : [],
            }
        ]
        return {'models':models},            

    async def nvidia_models(self):
        post                            = await self.get_post()
        api_key                         = post.get('api_key') or ''
        base_url                        = "https://integrate.api.nvidia.com/v1"
        client                          = OpenAI(
            api_key                     = api_key,
            base_url                    = base_url,
        )
        models                          = []
        for m in await async_exec(client.models.list):
            if m.object == 'model':
                models.append({
                    'value'             : m.id,
                    'label'             : m.id,
                    'support'           : [],
                })
        return {'models':models},

    async def models(self):
        organization_id                 = await self.get_post('organization_id')
        if organization_id:
            organization                = await self.getOrganization(organization_id)
        else:
            organization                = self.organization
        if not organization:
            return {'models':[]},
        children                        = [
            {
                'value'         : 'qwen-plus',
                'label'         : '千问-plus',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'qwen2.5-14b-instruct-1m',
                'label'         : '千问2.5-14b',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'qwen-max-latest',
                'label'         : '千问-Max-latest',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'qwen-max',
                'label'         : '千问-Max',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'qwen-vl-plus',
                'label'         : '千问2.5-VL-72B',
                'support'       : ['text','vision'],
            },
            {
                'value'         : 'qwen-omni-turbo',
                'label'         : '千问-Omni-Turbo',
                'support'       : ['tools','text','vision'],
            },
            {
                'value'         : 'qwq-plus',
                'label'         : '千问-QwQ-Plus',
                'support'       : ['text'],
            },
            {
                'value'         : 'deepseek-r1',
                'label'         : 'deepseek-r1',
                'support'       : ['text'],
            },
            {
                'value'         : 'qwen-coder-plus-latest',
                'label'         : '千问-Coder-Pluslatest',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'qwen2.5-coder-32b-instruct',
                'label'         : '千问2.5-Coder-32B',
                'support'       : ['tools','text'],
            },
            {
                'value'         : 'text-embedding-v3',
                'label'         : 'text-embedding-v3',
                'support'       : ['embedding'],
            },
            {
                'value'         : 'cosyvoice-v1',
                'label'         : '声音复刻CosyVoice',
                'support'       : ['voice.clone','voice.create'],
            },
            {
                'value'         : 'wanx2.1-t2i-turbo',
                'label'         : '万相-文生图2.1-Turbo',
                'support'       : ['image.from_text'],
            },
            {
                'value'         : 'wanx2.1-t2i-plus',
                'label'         : '万相-文生图2.1-Plus',
                'support'       : ['image.from_text'],
            },
            {
                'value'         : 'wanx2.1-i2v-turbo',
                'label'         : '万相-图生视频2.1-Turbo',
                'support'       : ['video.from_image'],
            },
            {
                'value'         : 'wanx2.1-i2v-plus',
                'label'         : '万相-图生视频2.1-Plus',
                'support'       : ['video.from_image'],
            },
            {
                'value'         : 'wanx2.1-t2v-turbo',
                'label'         : '万相-文生视频2.1-Turbo',
                'support'       : ['video.from_text'],
            },
            {
                'value'         : 'wanx2.1-t2v-plus',
                'label'         : '万相-文生视频2.1-Plus',
                'support'       : ['video.from_text'],
            },
        ]
        models                          = []
        bailian                         = organization.settings.get('bailian',{})
        if bailian.get('enable',False):
            models.append({
                'value'                 : 'bailian',
                'label'                 : '阿里云百炼',
                'children'              : children,
            })
        ollama                          = organization.settings.get('ollama',{})
        if ollama.get('enable',False):
            models.append({
                'value'                 : 'ollama',
                'label'                 : 'Ollama',
                'children'              : ollama['models'],
            })
        nvidia                          = organization.settings.get('nvidia',{})
        if nvidia.get('enable',False):
            models.append({
                'value'                 : 'nvidia',
                'label'                 : 'Nvidia',
                'children'              : nvidia['models'],
            })
        ragflow                         = organization.settings.get('ragflow',{})
        if ragflow.get('enable',False):
            models.append({
                'value'                 : 'ragflow',
                'label'                 : 'RAGFlow',
                'children'              : ragflow['models'],
            })
        
        other                           = organization.settings.get('other',{})
        if other.get('enable',False):
            models.append({
                'value'                 : 'other',
                'label'                 : '其他',
                'children'              : other['models'],
            })
        return {'models':models},