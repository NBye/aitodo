from __future__ import annotations
import uuid,importlib,re,traceback,json
from datetime import datetime

from src.super.ESModel import ESModel
from src.entity.ECache import ECache
from src.entity.EUserAction import EUserAction
from src.entity.EUserActionAgent import Agent

from src.utils.funcs import md5,log,text_indent
from src.utils.errors import CodeError
from src.utils.Datetime import Datetime

from src.utils.Template import Template

import config

class EUser(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score','balance','password','phone','email','username','authentication']
    DEFAULT_ATTRVALUES                  = {
        'balance'                       : 0.0,
        'gender'                        : '--',
        'salary'                        : {
            'y'                         : { 
                'enable'                : False,
                'price'                 : 0.0,
            },
            'm'                         : { 
                'enable'                : False,
                'price'                 : 0.0,
            },
            'd'                         : { 
                'enable'                : False,
                'price'                 : 0.0,
            },
            'h'                         : { 
                'enable'                : True,
                'price'                 : 0.0,
            },
        },
        'role'                          : 'user',
        'settings'                      : {
            'model'                     : ['',''],
            'visionmodel'               : ['',''],
            'textmodel'                 : ['',''],

            'opening_speech'            : '',
            'prompts'                   : "",

            'temperature'               : 0.7,
            'num_ctx'                   : 4096,
            'max_iterations'            : 1,
            'message_size'              : 20,
            'thoughtful'                : 5,
            'storage_limit'             : 1024.0,

            'definition'                : '',
            'template_related_me'       : '',
            'template_checkreply'       : '',
            'template_recprompts'       : '',
            'template_understand'       : '',
            'template_embeddings'       : '',
        },
        'authentication'                : {},
        'disabled'                      : False,
        'public'                        : True,
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
                "avatar"                : {"type": "keyword","index":False},
                "nickname"              : {"type": "text"},
                "gender"                : {"type": "keyword"},                      # 男 xy，女是 xx 
                "birthday"              : {"type": "date","format": "yyyy-MM-dd"},
                "slogan"                : {"type": "text","index":False},
                "introduction"          : {"type": "text"},                         # 介绍markdown文本格式
                "fashionshow"           : {"type": "keyword","index":False},        # 时尚秀地址

                "balance"               : {"type": "float"},                        # 个人账户余额
                "salary"                : {"type": "object"},                       # 薪水设置

                "phone"                 : {"type": "keyword"},
                "email"                 : {"type": "keyword"},
                "username"              : {"type": "keyword"},
                "password"              : {"type": "keyword","index": False},

                "disabled"              : {"type": "boolean"},
                "disabled_reason"       : {"type": "text"},

                "role"                  : {"type": "keyword"},                      # user,assistant
                "public"                : {"type": "boolean"},                      # 是否公开, 润许外部雇佣
                "authentication"        : {"type" : "object"},                      # 实名认证预留
                "settings"              : {
                    "type"              : "object",
                    "properties"        : {
                        "storage_limit" : {"type" : "float"},                       # 个人存储Gb数
                        "opening_speech": {"type" : "text", "index":False},         # 开场对话
                        "prompts"       : {"type" : "text", "index":False},         # 提示词换行隔开多条

                        "model"         : {"type" : "keyword"},                     # 模型名称
                        "visionmodel"   : {"type" : "keyword"},                     # 视觉模型

                        "temperature"   : {"type" : "float"},                       # 创意温度
                        "num_ctx"       : {"type" : "integer"},                     # 上下文长度
                        "max_iterations" : {"type" : "integer"},                    # 最大自检迭代次数
                        
                        "message_size"  : {"type" : "integer"},                     # 对话记忆长度
                        "thoughtful"    : {"type" : "integer"},                     # 思考周全成都
                        
                        "definition"            : {"type" : "text","index":False},  # 人设定义
                        "template_related_me"   : {"type" : "text","index":False},  # 涉及感知模板
                        "template_checkreply"   : {"type" : "text","index":False},  # 深度迭代模板
                        "template_recprompts"   : {"type" : "text","index":False},  # 深度迭代模板
                        "template_understand"   : {"type" : "text","index":False},  # 
                        "template_embeddings"   : {"type" : "text","index":False},  # 嵌入模板模式1
                    }
                },
                
                "creator_organization_id"           : {"type": "keyword"},          # 创造组织
                "creator_user_id"                   : {"type": "keyword"},          # 创造个人

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }
    @classmethod
    async def create(cls,refresh=True,virtual=False,**attrs):
        if not attrs.get('birthday',None):
            attrs['birthday']           = datetime.now().strftime("%Y-%m-%d")
        user                            = await super().create(refresh=refresh,virtual=virtual,**attrs)
        # 如果人类则，创建个人组织
        if virtual==False and user.role == 'user':
            from src.entity.EOrganization import EOrganization
            try:
                await EOrganization.create(refresh=refresh,virtual=virtual,user=user,
                    name                = (user.nickname[-4:] if '***' in user.nickname else user.nickname)+'的个人组织',
                )
            except BaseException as e:
                await user.destroy()
                raise e
        return user

    @classmethod
    async def login(cls, type, phone=None, email=None, username=None, password=None, img_code=None, img_code_id=None, phone_code=None, phone_code_id=None, email_code=None, email_code_id=None, token=None):
        if type=='0':
            data                        = await ECache.getData(token)
            if data==None or data.get('user_id',None)==None:
                await ECache.delData(token)
                raise CodeError(f'登录过期',401)
            user                        = await cls.afrom(data.get('user_id',None))
            if user==None:
                await ECache.delData(token)
                raise CodeError('无效Token',401)
            return token, user, data
        elif type=='1':
            if img_code != await ECache.getOnceData(img_code_id,'code'):
                raise CodeError('图片验证码无效')
            user                        = await cls.afrom(phone=phone,password=password)
        elif type=='2':
            if img_code != await ECache.getOnceData(img_code_id,'code'):
                raise CodeError('图片验证码无效')
            user                        = await cls.afrom(email=email,password=password)
        elif type=='3':
            if img_code != await ECache.getOnceData(img_code_id,'code'):
                raise CodeError('图片验证码无效')
            user                        = await cls.afrom(username=username,password=password)
        elif type=='4':
            cache                       = await ECache.getData(phone_code_id)
            c1      = cache.get('code',None)
            if not cache or phone_code != cache.get('code',None) or phone != cache.get('phone',None):
                raise CodeError(f'手机验证码无效')
            user                        = await cls.afrom(phone=phone)
            if user==None:
                user                    = await cls.create(
                    refresh             = 'true',
                    nickname            = phone[-11:-8] + "***" + phone[-4:],
                    phone               = phone,
                )
            await ECache.delData(phone_code_id)
        elif type=='5':
            cache                       = await ECache.getData(email_code_id)
            if not cache or email_code != cache.get('code',None) or email != cache.get('email',None):
                raise CodeError('邮箱验证码无效')
            user                        = await cls.afrom(email=email)
            if user==None:
                user                    = await cls.create(
                    refresh             = 'true',
                    nickname            = email.split('@')[0],
                    email               = email,
                )
            await ECache.delData(email_code_id)
        else:
            raise CodeError('不支持的登陆方式')
        if user==None:
            raise CodeError('找不到该用户')
        elif user.disabled:
            raise CodeError('用户被禁用')
        token                           = str(uuid.uuid4())
        # 只有一个组织时候默认进入
        query                           = {
            "bool"                      : {"must":[
                {"term": {"disabled": False}},
                {"term": {"user_id": user._id}},
            ]},
        }
        from src.entity.EOrganizationUser import EOrganizationUser
        organizations ,_                = await EOrganizationUser.search(query=query,_source="created,organization_id".split(','))
        if len(organizations) == 1:
            await ECache.setData(token, 3600*24*7,refresh=True,
                user_id                 = user._id,
                organization_id         = organizations[0].organization_id
            )
        else:
            await ECache.setData(token, 3600*24*7,refresh=True,
                user_id                 = user._id,
            )
        return token, user, {}

    async def to_safe_dict(self):
        join_info                       = self.get('join_info',{}) or {}
        return {
            '_id'                       : self._id,
            'role'                      : self.role,
            'avatar'                    : self.avatar,
            'nickname'                  : self.nickname,
            'gender'                    : self.gender,
            'birthday'                  : self.birthday,
            'slogan'                    : self.slogan,
            'join_info'                 : {k:join_info.get(k,'') for k in ['aliasname','remark','created']  },
            'action_list'               : [{'name':a.get('name'),'description':a.get('description'),} for a in self.get('action_list',[])],
        }

    def is_system_admin(self):
        if not config.SYSTEM_ADMIN_USER_IDS:
            return True
        return self._id in config.SYSTEM_ADMIN_USER_IDS

    # 与我相关
    async def related_me(self,message:EChatMessage,messages:list[EChatMessage]):
        prompt                          = await Template(
            self.settings.get('template_related_me') or config.TEMPLATE_RELATED_ME,
            messages                    = [await m.to_safe_dict() for m in messages],
            message                     = await message.to_safe_dict(),
            assistant                   = await self.to_safe_dict(),
        )
        async for data,tokens in self.execute_model('Generate.generate',prompt=prompt,stream=False,temperature=0):
            if re.search(f'yes', data['content'], re.IGNORECASE | re.DOTALL):
                # print(f"^ related_me: {self.nickname} True: \n{data['content']}")
                return True
            else:
                # print(f"^ related_me: {self.nickname} False: \n{data['content']}")
                return False

    # 与我相关
    async def check_reply(self,message:EChatMessage,messages:list[EChatMessage],reply:EChatMessage):
        prompt                          = await Template(
            self.settings.get('template_checkreply') or config.TEMPLATE_CHECKREPLY,
            messages                    = [await m.to_safe_dict() for m in messages],
            message                     = await message.to_safe_dict(),
            assistant                   = await self.to_safe_dict(),
            reply                       = await reply.to_safe_dict(),
        )
        async for data,tokens in self.execute_model('Generate.generate',prompt=prompt,stream=False,temperature=0):
            if re.search(f'yes', data['content'], re.IGNORECASE | re.DOTALL):
                # print(f"^ check_reply: {self.nickname} True: \n{data['content']}")
                return True
            else:
                # print(f"^ check_reply: {self.nickname} False: \n{data['content']}")
                return data['content']
    
    # 获取推荐提示词
    async def recommend_prompts(self,message:EChatMessage,messages:list[EChatMessage],reply:EChatMessage):
        prompts                         = self.settings.get('prompts') or ''
        if not prompts:
            return []
        prompt                          = await Template(
            self.settings.get('template_recprompts') or config.TEMPLATE_RECPROMPTS,
            messages                    = [await m.to_safe_dict() for m in messages],
            message                     = await message.to_safe_dict(),
            assistant                   = await self.to_safe_dict(),
            reply                       = await reply.to_safe_dict(),
            prompts                     = prompts
        )
        async for data,tokens in self.execute_model('Generate.generate',prompt=prompt,stream=False,temperature=0):
            try:
                return json.loads(data['content'])
            except Exception:
                print(f"recommend_prompts error: {data['content']}")
        return []

    # 意图识别
    async def chat_reading(self,chat:EChat,message:EChatMessage,messages:list[EChatMessage],reply:EChatMessage):
        from src.entity.EChatMessage import EChatMessage
        from src.entity.EUserActionAgent import Agent
        agent_list                      = []
        for action in self.action_list:
            for agent in action.agent_list:
                agent['action']         = action
                agent_list.append(agent)

        for efile in message.files:
            if agent:= Agent.init(chat=chat,user=self,file_id=efile._id,**efile):
                agent_list.append(agent)
      
        max_iterations                  = self.settings.get('max_iterations',1)
        iteration_index                 = 0
        total_prompt_tokens             = 0     # 请求token总计
        replys                          = []
        unique_cahce                    = {}
        while iteration_index < max_iterations:
            iteration_index            += 1
            print('|||','iteration_index',iteration_index, '|' * 50)
            total_output_tokens         = 0     # 输出token总计
            total_content               = ''    # 汇总返回内容
            async for data,prompt_tokens in Agent(chat=chat,user=self,name='root',description='最终合并结果答问题',children=agent_list).execute(message,messages,reply,replys=replys,unique_cahce=unique_cahce):
                total_prompt_tokens     += prompt_tokens
                total_output_tokens    += data.get('tokens',0)
                total_content          += data.get('content','')
                status                  = data.get('status')
                overd                   = status in ['completed','incomplete']
                status_map              = dict(
                    completed           = '生成完毕',
                    incomplete          = '生成中断',
                    in_progress         = '生成中...' if data.get('content','') else '正在思考中...',
                )
                status                  = 'in_progress'
                await reply.upset(
                    embeddings          = reply.embeddings+data.get('embeddings',[]),
                    refresh             = overd,
                    content             = total_content,
                    status              = status,
                    status_description  = data.get('status_description') or status_map.get(status),
                    completed           = Datetime.afrom().format(),
                    tokens              = total_output_tokens
                )
                yield data.get('content','')
            if iteration_index < max_iterations:
                reply.status_description = '正在思考是否补充...'
                yield ''
                proposal = await self.check_reply(message=message,messages=messages+replys,reply=reply)
                if proposal==True:
                    break
                await reply.log(list=[proposal],remark="思考补充")
                await reply.upset(status='completed',status_description='生成完毕')
                yield ''
                replys.append(reply)
                replys.append(await EChatMessage.virtual(role='user',content=proposal))
                reply.update(await EChatMessage.create(
                    chat_id             = chat._id,
                    user_id             = self._id,
                    user_nickname       = self.nickname,
                    user_avatar         = self.avatar,
                    user_gender         = self.gender,
                    role                = self.role,
                    status              = 'in_progress',
                ))
            else:
                break
        await reply.upset(status='completed',status_description='生成完毕')
        await message.upset(tokens=total_prompt_tokens)
        yield ''

        if self.settings.get('prompts'):
            prompts                     = await self.recommend_prompts(message=message,messages=messages+replys,reply=reply)
            if prompts:
                print(prompts)
                await reply.upset(prompts=prompts)
                yield ''


    # 获取消息的理解
    async def get_understand(self,message,messages):
        if message.understand:
            return message.understand
        from src.entity.EChatMessage import EChatMessage
        understand                      = ''
        if len(messages) == 0:
            understand                  = message.content
        else:
            prompt                      = await Template(
                self.settings.get('template_understand') or config.TEMPLATE_UNDERSTAND,
                messages                = [await m.to_safe_dict() for m in messages],
                message                 = await message.to_safe_dict(),
                user                    = await self.to_safe_dict(),
            )
            async for data,tokens in self.execute_model('Generate.generate',prompt=prompt,stream=False,temperature=0):
                understand              = data['content']
        if understand:
            await message.upset(understand=understand)
        return understand

    # 执行模型
    async def execute_model(self,module,strict=False,**options):
        try:
            model                       = options.get('model') or self.settings.get('model')
            if isinstance(model, str):
                platform, modelname     = tuple(model.split(".", 1))
            else:
                platform, modelname     = tuple(model)
            moduleName, attrName        = tuple(module.split(".", 1))
            module                      = importlib.import_module(f"src.utils.model.{platform}.{moduleName}")
            if options.get('model'):
                del options['model']
            options                     = {
                "temperature"           : options.get('temperature') or self.settings.get('temperature',0.7),
                "num_ctx"               : options.get('num_ctx') or self.settings.get('num_ctx',4096),
                **options
            }
            from src.entity.EOrganization import EOrganization
            organization                = await EOrganization.afrom(_id=self.creator_organization_id)
            async for data in getattr(module, attrName)(modelname,organization=organization,user=self,**options):
                yield data
        except BaseException as e:
            if isinstance(e, GeneratorExit):
                pass
            elif strict:
                raise e
            else:
                yield {
                    "role"              : 'assistant',
                    "content"           : f'```\n{str(e)}\n{traceback.format_exc()}\n```', 
                    "tokens"            : 0, #回答token数
                    "status"            : "incomplete"
                }, 0

    async def call_model(self,model=None,action=None,platform=None,moduleName=None,module=None,method=None,organization=None,**parameters):
        if model:
            platform,moduleName         = tuple(model)
        if action:
            module,method               = tuple(action.split('.',1))
        # print(f"src.utils.model.{platform}.{module.capitalize()}",method,parameters)
        module                          = importlib.import_module(f"src.utils.model.{platform}.{module.capitalize()}")
        if not organization:
            organization                = await self.get_creator_organization()
        return await getattr(module, method)(model=moduleName,user=self,organization=organization,**parameters)

    def get_setting_model(self,name):
        return self.settings.get(name) or self.DEFAULT_ATTRVALUES['settings'][name] or self.settings.get('model') or self.DEFAULT_ATTRVALUES['settings']['model'] 

    async def get_creator_organization(self):
        from src.entity.EOrganization import EOrganization
        return await EOrganization.afrom(_id=self.creator_organization_id)

    async def opening_answer(self,chat):
        if self.settings['opening_speech'].strip():
            prompts                     = self.settings.get('prompts') or None
            print(prompts,self.settings)
            from src.entity.EChatMessage import EChatMessage
            return await EChatMessage.create(
                chat_id                 = chat._id,
                user_id                 = self._id,
                user_nickname           = self.nickname,
                user_avatar             = self.avatar,
                user_gender             = self.gender,
                role                    = self.role,
                status                  = 'completed',
                prompts                 = prompts.split('\n')[0:5] if prompts else [],
                content                 = self.settings['opening_speech']
            )

class EAssistant(EUser):
    INDEX_NAME                          = 'user'

class EAtUser(EUser):
    def __init__(self,user:EUser):
        self.nickname                   = user.nickname
        self.aliasname                  = user.get('join_info',{}).get('aliasname','')
        self.avatar                     = user.avatar
        self.gender                     = user.gender
        self._id                        = user._id