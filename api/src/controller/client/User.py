from quart import request
from src.super.controllers import ClientController

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser

from src.entity.EFile import EFile
from src.entity.ECache import ECache
from src.utils.funcs import md5
from src.utils.errors import CodeError

import json,shutil

class User(ClientController):

    VERIFY_LIST                         = [
        ('nickname',    [0,20],     None,   '昵称需要20个字符以内'),
        ('birthday',    [10,10],    None,   '生日格式yyyy-mm-dd'),
        ('gender',      [2,4],      None,   '性别为 xx 或 xy'),
        ('slogan',      [0,200],    None,   '口号需要200个字符以内'),
        ('introduction',[0,20000],  None,   '简介不得超过两万个字符'),
    ]

    async def logout(self):
        await ECache.delData(self.token)
        return {},'退出成功',401

    async def info(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        organization_id                 = post.get('organization_id',None)
        organization                    = None
        if user_id:
            user                        = await EUser.afrom(user_id,_must=True)
            storage_count               = 0
            if organization_id:
                _source                 = ['user_id','aliasname','created','reception_status','disabled','disabled_reason','remark','expired']
                ou                      = await EOrganizationUser.afrom(user_id=user_id,organization_id=organization_id)
                if not ou:
                    user['join_info']   = None
                else:
                    user['join_info']   = ou.desensitization()
                    aggs                = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
                        {"term": {"user_id": user_id}},
                    ]}})
                    storage_count       = (aggs['total_size']['value'])/(1024**3)
            if user.creator_organization_id:
                organization            = await self.getOrganization(user.creator_organization_id)
        else:
            user                        = self.user
            if self.session.get('organization_id',None):
                organization            = await EOrganization.afrom(_id=self.session['organization_id'])
            aggs                        = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
                {"term": {"user_id": user._id}},
            ]}})
            storage_count               = (aggs['total_size']['value'])/(1024**3)
            
        return {
            'user'                      : user.desensitization(),
            'organization'              : organization,
            'storage_count'             : storage_count,
            'is_system_admin'           : user.is_system_admin(),
        },

    async def disabled(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        organization_id                 = post.get('organization_id',None)
        disabled                        = post.get('disabled',None) or False
        disabled_reason                 = post.get('disabled_reason','')
        # 组内禁用
        if organization_id:
            organization                = await EOrganization.afrom(_id=organization_id)
            if not organization:
                raise CodeError('当前组织不存在')
            if self.user._id != organization.user_id:
                raise CodeError('无权限操作',403)
            ou                          = await EOrganizationUser.afrom(user_id=user_id,organization_id=organization_id)
            if not ou :
                raise CodeError('当前用户不在组织内')
            await ou.upset(disabled=bool(disabled),disabled_reason=disabled_reason)
        # 管理员解除禁止用户
        elif self.is_admin:
            user                        = await EUser.afrom(_id=user_id)
            if not user:
                raise CodeError('用户不存在')
            await user.upset(disabled=bool(disabled),disabled_reason=disabled_reason)
        else:
            raise CodeError('无权限',403)
        if disabled:
            return {},'禁用成功'
        else:
            return {},'解禁成功'

    async def upset(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        organization_id                 = post.get('organization_id',None)
        group                           = post.get('group',None)
        validation                      = {
            'base'                      : [
                ('nickname',    [2,20],     None,   '昵称需要20个字符以内'),
                ('birthday',    [10,10],    None,   '生日格式yyyy-mm-dd'),
                ('gender',      [2,2],      None,   '性别为 xx 或 xy'),
                ('slogan',      [0,200],    None,   '口号需要200个字符以内'),
                ('introduction',[0,20000],  None,   '简介不得超过两万个字符'),
                ('public',      [0,10],     None,   ''),
            ],
            'join'                      : [
                ('aliasname',   [0,20],     None,   '昵称需要20个字符以内'),
                ('remark',      [0,50],     None,   '用户备注最多50个字'),
                ('reception_status',      [0,50],     None,''),
            ],
            'settings'                  : [
                ('message_size',[1,1000],   None,   '详细长度最长1000条'),
                ('model',       [1,150],    None,   '请选择意图模型'),
                ('visionmodel', [1,200],    None,   '请选择视觉模型'),
                ('textmodel',   [1,200],    None,   '请选择语言模型'),
                ('num_ctx',     [0,20480],  None,   '上下文长度20480'),
                ('max_iterations',[0,20480],  None,  '最大自检迭代次数'),
                ('temperature', [0,1],      None,   '创意0~1之间'),
                ('thoughtful',  [0,50],     None,   '思维宽度0~50个字'),

                ('opening_speech',          [0,2000],   None,   '开场对话0~1000个字'),
                ('prompts',                 [0,2000],   None,   '提示词引导'),

                ('definition',              [0,2000],   None,   '人设定义0~2000个字'),
                ('template_related_me',     [0,2000],   None,   '涉及感知0~2000个字'),
                ('template_checkreply',     [0,2000],   None,   '深度迭代0~2000个字'),
                ('template_recprompts',     [0,2000],   None,   '推荐提问0~2000个字'),
                ('template_understand',     [0,2000],   None,   '深度理解模板0~2000个字'),
                ('template_embeddings',     [0,2000],   None,   '嵌入模板0~2000个字'),
            ],
            'account'                   : [
                # ('username',    [4,20],     None,   '账号长度为4~20个字符'),
                ('password',    [6,50],     None,   '密码长度为6~50个字符'),
            ]
        }
        user                            = self.user
        organization                    = None
        ou                              = None
        data                            = {}
        if organization_id:
            organization                = await self.getOrganization(organization_id)
            if not organization:
                raise CodeError('组织不存在')
        if user_id :
            user                        = await self.getUser(user_id)
            if not user:
                raise CodeError('用户不存在')
        if organization and user:
            ou                          = await EOrganizationUser.afrom(organization_id=organization_id,user_id=user_id)
            if not ou:
                raise CodeError('该用户不在组织内')
        if organization and not await EOrganizationUser.afrom(organization_id=organization_id,user_id=self.user._id):
            raise CodeError('无权限修改组织外用户信息',403)
        if user.role=='user' and user._id!=self.user._id:
            raise CodeError('只有自己才能修改自己的信息')

        # 修改基础信息
        if group=='base' :
            data                        = await self._check_data(None,validation[group])
            avatar                      = (await request.files).get('avatar')
            if avatar :
                remark                  = user.nickname + ' 的头像'
                efile                   = await EFile.upload(avatar, user,organization=None if user.role=='user' else organization, location='public',remark=remark)
                data['avatar']          = efile.url
            await user.upset(**data)
        # 修改加入信息
        elif  group=='join':
            data                        = await self._check_data(None,validation[group])
            await ou.upset(**data)
        # 修改参数设置
        elif group=='settings' or group=='template':
            data                        = await self._check_data(None,validation['settings'])
            for k in ['model','visionmodel','textmodel']:
                if not data[k]:
                    raise CodeError('请完善大模型设置')
            await user.upset(settings=data)
        elif group=='account':
            data                        = await self._check_data(None,validation[group])
            if data.get('password'):
                data['password']        = md5(data['password'])
            await user.upset(**data)
        else:
            raise CodeError('不支持的修改类型')
        user                            = user.desensitization()
        if ou:
            user['join_info']           = ou.desensitization()
        return {'user':user},'保存成功'

    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword','')
        organization_id                 = post.get('organization_id','')   #1 组织内搜索
        creator_organization_id         = post.get('creator_organization_id','')   #1 制造商id
        invited_organization_id         = post.get('invited_organization_id','')   #1 用户与改改组织ID是否加入
        public                          = post.get('public',None)
        role                            = str(post.get('role',''))
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',200))
        sort_list                       = await self.splitSortList()
        joins                           = {}
        query                           = {
            "bool"                      : {"must":[]},
        }
        if organization_id and invited_organization_id:
            raise CodeError('有参数不可同时传入')
        _ou_source                      = ['user_id','aliasname','created','disabled','disabled_reason','remark','expired']
        if organization_id:
            if not await EOrganizationUser.afrom(user_id=self.user._id,organization_id=organization_id):
                return {},'无权限查看该组织的成员',403
            ou_list,_                   = await EOrganizationUser.search(query={'term':{'organization_id':organization_id}},_source=_ou_source,track_total_hits=10000,size=1000)
            for ou in ou_list:
                joins[ou.user_id]       = ou
            if not joins:
                return {'list':[],'total':0},
            else:
                query['bool']['must'].append({'terms':{'_id':list(joins.keys())}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"nickname": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        if role:
            query["bool"]["must"].append({'term':{'role':role}})
        if isinstance(public, bool):
            query["bool"]["must"].append({'term':{'public':public}})
        _source                         = ["avatar","nickname",'birthday','gender','slogan','role']
        if creator_organization_id:
            query['bool']['must'].append({'term':{'creator_organization_id':creator_organization_id}})
        liss,total                      = await EUser.search(query=query,_source=_source,track_total_hits=10000,**{'from':skip,'size':size},sort=sort_list)
        
        if invited_organization_id:
            query                       = {
                "bool"                      : {"filter":[
                    {'term' : {'organization_id': invited_organization_id,}},
                    {'terms' : {'user_id': [user._id for user in liss],}},
                ]},
            }
            ou_list,_                   = await EOrganizationUser.search(query={'term':{'organization_id':organization_id}},_source=_ou_source,track_total_hits=10000,size=1000)
            for ou in ou_list:
                joins[ou.user_id]       = ou
        
        for i,user in enumerate(liss):
            liss[i]                     = user.desensitization()
            if joins and joins.get(user._id,None):
                liss[i]['join_info']    = joins[user._id].desensitization()
                del liss[i]['join_info']['_id']
            else:
                liss[i]['join_info']    = None

        return {'list':liss,'total':total},

    async def models(self):
        post                            = await self.get_post()
        user_id                         = post.get('user_id',None)
        assistant                       = await self.getUser(user_id)

  