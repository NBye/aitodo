from __future__ import annotations
import sys,time,uuid,math,importlib,json
from datetime import datetime,timedelta

from src.super.ESModel import ESModel
from src.entity.EUser import EUser
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EPayment import EPayment

from src.utils.funcs import md5,generateRole
from src.utils.errors import CodeError
from src.utils.U62Id import U62Id
from src.utils.Redis import Redis

import config

class EOrganization(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score','balance']
    DEFAULT_ATTRVALUES                  = {
        'slogan'                        : '欢迎加入',
        'disabled'                      : False,
        'balance'                       : 0.0,
        'authentication'                : {},
        'settings'                      : {
            "user_limit"                : 200,
            'embedmodel'                : ['',''],
            "storage_limit"             : 1024.0,
            "join_code_enabled"         : False,
            "join_code_value"           : '',
            "join_invite_enabled"       : True,
        },
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
                "avatar"                : {"type": "keyword","index":False},
                "name"                  : {"type": "text","fields": {"keyword": {"type": "keyword" }}},
                "slogan"                : {"type": "text","index":False},
                "introduction"          : {"type": "text"},                     # 介绍markdown文本格式
                "balance"               : {"type": "float"},

                "disabled"              : {"type": "boolean"},
                "disabled_reason"       : {"type": "text"},
   
                "authentication"        : {"type" : "object"},                  # 实名认证预留

                "join_method"           : {"type": "object","enabled": False},
                "settings"              : {
                    "type"              : "object",
                    "properties"        : {
                        "embedmodel"            : {"type": "keyword"},           # 嵌入模型名称
                        "user_limit"            : {"type": "integer"},
                        "storage_limit"         : {"type": "float"},
                        "join_code_enabled"     : {"type": "boolean"},
                        "join_code_value"       : {"type": "keyword"},
                        "join_invite_enabled"   : {"type": "boolean"},
                    }
                },
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def create(cls,refresh=True,virtual=False,user=None,**attrs):
        if user==None:
            raise CodeError('User 对象不能为 Null')
        attrs['user_id']                = user._id
        organization                    = await super().create(refresh=refresh,virtual=virtual,**attrs)
        try:
            # 进入组织
            await organization.join(user,'创建者')
            # 创建第一个AI
            nickname,gender,avatar      = generateRole()
            assistant                   = await EUser.create(
                refresh                 = True,
                nickname                = nickname,
                gender                  = gender,
                avatar                  = avatar,
                birthday                = datetime.now().strftime("%Y-%m-%d"),
                slogan                  = '您的AI助理，用心倾听，用智服务，为您提供贴心高效的解决方案！',
                introduction            = '你是一个中文小秘书',
                role                    = 'assistant',
                public                  = False,
                creator_organization_id = organization._id,
                creator_user_id         = user._id,
            )
            await organization.join(assistant,remark='我的定制小秘书')
        except BaseException as e:
            await organization.destroy()
            raise e
        try:
            if config.HIRE_ASSISTANT_IDS:
                for assistant_id in config.HIRE_ASSISTANT_IDS.split(','):
                    assistant           = await EUser.afrom(_id=assistant_id)
                    if assistant:
                        await organization.join(assistant,remark='平台推荐小秘书')
        except BaseException as e:
            pass
        return organization

    # 删除数据
    async def destroy(self,refresh=True):
        from src.entity.EFile import EFile
        query                           = {'term':{'organization_id':self._id}}
        # 1. 删除文件
        while True:
            files,_                     = await EFile.search(query=query)
            if len(files):
                for ef in files:
                    await ef.destroy()
            else:
                break
        # 2. 清退用户
        await EOrganizationUser.destroyMany(query=query)
        # 3. 删除组织
        await super().destroy(refresh=refresh)
        return True

    # 转化向量
    async def text_to_vector(self,text):
        model                           = self.settings.get('embedmodel')
        if isinstance(model, str):
            platform, modelname         = tuple(model.split(".", 1))
        else:
            platform, modelname         = tuple(model)
        module                          = importlib.import_module(f"src.utils.model.{platform}.Embed") 
        return await module.embed(modelname,text,organization=self)

    async def join(self,user:EUser, remark:str='',salary=None,expired=None)->EOrganizationUser:
        count                           = await EOrganizationUser.count(query={'term':{'organization_id':self._id}})
        if count >= self.settings['user_limit']:
            raise CodeError(f"组织人数已达上限({self.settings['user_limit']})")
        ue                              = await EOrganizationUser.afrom(organization_id=self._id,user_id=user._id)
        if ue:
            raise CodeError('该用户已加入')
        eu                              = await EOrganizationUser.create(
            organization                = self,
            user                        = user,
            refresh                     = True,
            remark                      = remark,
            expired                     = expired,
            salary                      = salary,
        )
        return eu

    async def getJoinInfo(self,user:EUser=None,user_id=None):
        if user_id:
            info                        = await EOrganizationUser.afrom(organization_id=self._id, user_id=user_id)
        elif user:
            info                        = await EOrganizationUser.afrom(organization_id=self._id, user_id=user._id)
        else:
            raise CodeError('未指定用户ID')
        return info
   
    async def leave(self,user:EUser):
        if self.user_id == user._id:
            raise CodeError('组织的创建者不能离开')
        if user.role=='assistant' and user.creator_organization_id == self._id:
            raise CodeError('当前组织创建的AI，不可以移除。')
        ue                              = await EOrganizationUser.afrom(organization_id=self._id,user_id=user._id)
        if not ue:
            raise CodeError('用户未在当前组织中')
        await ue.destroy()

    async def storage_total(self):
        from src.entity.EFile import EFile
        from src.entity.EKnowledge import EKnowledge
        total                           = 0
        aggs                            = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
            {"term": {"organization_id": self._id}},
        ]}})
        total                           += aggs['total_size']['value']
        aggs                            = await EKnowledge.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
            {"term": {"organization_id": self._id}},
        ]}})
        total                           += aggs['total_size']['value']
        return total
    
    async def import_knowledge(self,text,user,batch=None, chunk_size=256,chunk_overlap=None,**data):
        from src.entity.EKnowledge import EKnowledge
        # 判断容量
        total                           = await self.storage_total()/(1024**3)
        limit                           = self.settings.get('storage_limit',0)
        if total >= self.settings.get('storage_limit',0):
            raise CodeError(f'当前组织存储不足{round(total,1)}/{limit}GB,请删除一些文件或知识。')
        if not batch:
            batch                       = U62Id.generate(16)
        if not chunk_overlap:
            chunk_overlap               = int(chunk_size*0.2)
        if not data.get('knowledge_bucket_id',None):
            raise CodeError('缺少参数')
        serial,start,length             = 0,0,len(text)
        while start < length:
            end                         = min(start + chunk_size, length)
            data['text']                = text[start:end]
            data['user_id']             = user._id
            data['organization_id']     = self._id
            data['serial']              = serial
            data['batch']               = batch

            vector,tokens               = await self.text_to_vector(data['text'])
            data['query_vector']        = vector
            data['query_tokens']        = tokens
            data['size']                = len(data['text'].encode('utf-8')) * 8

            knowledge                   = await EKnowledge.create(**data)
            start                       += chunk_size - chunk_overlap
            serial                      += 1
            yield knowledge
    
    # 发起支付
    async def recharge(self,user,amount):
        payment                         = await EPayment.create(
            user_id                     = user._id,
            organization_id             = self._id,
            remark                      = '组织账户储值',
            scene                       = 'recharge',
            amount                      = amount,
        )
        data                            = await payment.pay()
        if data['code']!=1:
            raise CodeError(data['msg'],data['code'],data['data'])
        return data['data']

    async def get_balance(self):
        k                               = f'{self._id}_balance'
        r                               = Redis(scene='organization')
        balance                         = await r.get(k)
        if balance==None:
            balance                     = self.balance
            await r.set(k,balance)
        else:
            balance                     = float(balance)
        self.balance                    = round(balance,2)
        return self.balance

    async def inc_balance(self,amount):
        # self.get_balance()
        k                               = f'{self._id}_balance'
        r                               = Redis(scene='organization')
        balance                         = await r.incrbyfloat(k,float(amount))
        balance                         = round(balance, 2)
        await self.upset(balance=balance)
        return balance

    async def consume(self,amount,remark='消费',user=None,overdraft=False):
        if amount <= 0:
            raise CodeError('消费金额必须大于0')
        self.balance                    = await self.get_balance()
        balance                         = self.balance - amount
        if balance<0 and overdraft==False:
            raise CodeError('组织账户余额不足',code=406,data={'balance':self.balance,'consume':amount})
        payment                         = await EPayment.create(
            user_id                     = user._id if user else '',
            organization_id             = self._id,
            remark                      = remark,
            scene                       = 'consume',
            amount                      = 0.0-amount,
            status                      = 'paying'
        )
        after                           = await self.inc_balance(0-amount)
        data                            = {
            'after'                     : after,
            'before'                    : round(after+amount,2),
        }
        await payment.upset(status='success',data=data,completed=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return payment

    async def commission(self,amount,remark='分佣'):
        if amount <= 0:
            raise CodeError('佣金金额必须大于0')
        self.balance                    = await self.get_balance()
        balance                         = self.balance + amount
        payment                         = await EPayment.create(
            user_id                     = '',
            organization_id             = self._id,
            remark                      = remark,
            amount                      = amount,
            scene                       = 'commission',
            status                      = 'paying',
        )
        after                           = await self.inc_balance(0+amount)
        data                            = {
            'after'                     : after,
            'before'                    : round(after-amount,2),
        }
        await payment.upset(status='success',data=data,completed=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return payment


    async def event_listen(self):
        k                               = f'organization_{self._id}_event'
        r                               = Redis(scene='organization_event')
        n                               = 0
        s                               = datetime.now().strftime("%Y%m%d%H%M%S")
        async with r.pubsub() as pubsub:
            await pubsub.subscribe(k)
            async for message in pubsub.listen():
                if message.get('type') == 'message':
                    n                   = n + 1
                    data                = json.loads(message['data'])
                    data['id']          = f'{s}_{n}'
                    yield data

    async def event_publish(self,event,data):
        k                               = f'organization_{self._id}_event'
        r                               = Redis(scene='organization_event')
        await r.publish(k, json.dumps({'event':event,'data':data}))