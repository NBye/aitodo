from __future__ import annotations
import time,uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta

from src.super.ESModel import ESModel
from src.entity.ECache import ECache
from src.entity.EUser import EUser

from src.utils.funcs import md5
from src.utils.errors import CodeError

import config

class EOrganizationUser(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score','balance']
    DEFAULT_ATTRVALUES                  = {
        'balance'                       : 0.0,
        'disabled'                      : False,
        'salary'                        : {
            'type'                      : 'h',
            'price'                     : 0.0,
            'settlement'                : 'auto'
        },
        'expired'                       : None,
        'reception_status'              : False,
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
                "organization_id"       : {"type": "keyword"},
                "user_id"               : {"type": "keyword"},
                "user_role"             : {"type": "keyword"},
                "aliasname"             : {"type": "text"},             # 别名
                "balance"               : {"type": "float"},            # 组织内账户

                "salary"                : {                             # 雇佣薪酬
                    "type"              : "object",
                    "properties"        : {
                        "type"          : {"type" :"keyword"},          # 计费周期
                        "price"         : {"type" :"float"},            # 积分金额
                        "settlement"    : {"type": "keyword"},          # manual|auto
                    }
                },

                "disabled"              : {"type": "boolean"},
                "disabled_reason"       : {"type": "text"},

                "reception_status"      : {"type": "boolean"},          # 接待状态

                "remark"                : {"type": "text", "index": False}, #加入备注
                "expired"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }
   
    @classmethod
    async def create(cls,organization,user,refresh=False,virtual=False,salary=None,**attrs):
        if salary:
            attrs['salary']             = salary
        attrs['organization_id']        = organization._id
        attrs['user_id']                = user._id
        attrs['user_role']              = user.role
        
        # 人类都是无线时间的
        if user.role == 'user':
            attrs['expired']            = None
        # 组织雇佣自己创建的也室无限时间
        elif user.role == 'assistant' and organization._id == user.creator_organization_id:
            attrs['expired']            = None
        # 付费雇佣则需要支付，否则上来就睡了。
        elif user.role == 'assistant' and salary and salary['price']>0:
            attrs['expired']            = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 非雇佣的默认测试时间
        elif user.role == 'assistant' and not salary: # 默认免费用
            attrs['expired']            = None
        ou                              = await super().create(refresh=refresh,virtual=virtual,**attrs)
        try:
            if user.role == 'assistant' and ou.salary['price']>0:
                await ou.salary_settlement(organization=organization,user=user,strict=True)
        except Exception as e:
            await ou.destroy()
            raise e
        return ou

    async def salary_settlement(self,organization=None,user=None,creator_organization=None,type=None,price=None,strict=False):
        from src.entity.EOrganization import EOrganization
        if not organization:
            organization                = await EOrganization.afrom(_id=self.organization_id)
        if not user:
            from src.entity.EUser import EUser
            user                        = await EUser.afrom(_id=self.user_id)
        # 人类不需要续费结算工资
        if user.role == 'user':
            return True
        # 自己雇佣自己无需结算
        if organization.user_id == user._id:
            return True
        # 自己雇佣自己创建的AI无需结算
        if organization._id == user.creator_organization_id:
            return True
        if type:
            salary                      = user.salary[type]
            price                       = price or self.salary['price']
            self.salary['type']         = type
            self.salary['price']        = salary['price']
        else:
            salary                      = user.salary[self.salary['type']]
            price                       = self.salary['price']
        # 无限期的不用续费    
        if self.expired==None:
            return True
        try:
            if not salary['enable']:
                raise CodeError('当前雇佣方式已停用，请手动结算工资。')
            if salary['price'] != price:
                raise CodeError('当前雇价格发生变化，请手动结算工资。')
            if salary['price'] > 0:
                await organization.consume(amount=salary['price'],remark=f'结算工资: {user.nickname}')
                if creator_organization == None and user.creator_organization_id:
                    creator_organization= await EOrganization.afrom(_id=user.creator_organization_id)
                    if creator_organization:
                        service_fee     = round(salary['price']*0.2, 2) or 0.01
                        await creator_organization.commission(amount=salary['price']-service_fee,remark=f'AI租售佣金，服务费:{service_fee}')
            now                         = datetime.now()
            ctime                       = datetime.strptime(self.expired, "%Y-%m-%d %H:%M:%S")
            if ctime < now:
                ctime                   = now
            date                        = ctime + relativedelta(hours=1)
            if   self.salary['type'] == 'y':
                date                    = ctime + relativedelta(years=1)
            elif self.salary['type'] == 'm':
                date                    = ctime + relativedelta(months=1)
            elif self.salary['type'] == 'd':
                date                    = ctime + relativedelta(days=1)
            await self.upset(refresh=True,salary=self.salary,expired=date.strftime("%Y-%m-%d %H:%M:%S"))
            return True
        except Exception as e:
            # 结算异常改为手动
            if self.salary['settlement']=='auto':
                self.salary['settlement']='manual'
                await self.upset(refresh=False,salary=self.salary)
            if strict:
                raise e 
            else:
                return False
            
