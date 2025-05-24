from src.super.controllers import ContableController
from src.utils.errors import CodeError
from src.utils.funcs import log
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.entity.EOrganizationUser import EOrganizationUser
import traceback

class User(ContableController):

    async def auto_salary_settlement(self):
        # 一次最多处理100个
        adjuste,success,failure         = 0,0,0

        # 过期1个月以上 + 自动结算的 = 转为手动结算
        query                           = {
            "bool"                      : {"must":[
                {'term':{"user_role":"assistant"}},
                {'term':{"salary.settlement":"auto"}},
                {'range':{"expired":{
                    "lte"               : (datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")
                }}},
            ]},
        }
        script                          = {
            "source"                    : "ctx._source.salary.settlement = 'manual'",
            "lang"                      : "painless"
        }
        adjuste                         = await EOrganizationUser.upsetMany(refresh=True,query=query,script=script)
        # 过期|即将过期 + 自动结算的，扣除账号结算。
        query                           = {
            "bool"                      : {"must":[
                {'term':{"salary.settlement":"auto"}},
                {'term':{"user_role":"assistant"}},
                {'range':{"expired":{
                    "gte"               : (datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    "lte"               : (datetime.now() + relativedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                }}}
            ]},
        }
        list,_                          = await EOrganizationUser.search(query=query,size=1000)
        for ou in list:
            try:
                if await ou.salary_settlement(strict=True):
                    success             += 1
                else:
                    failure             += 1
            except Exception as e:
                failure                 += 1
                await log(str(e) + '\n' + traceback.format_exc())

        return {'adjuste':adjuste,'success':success,'failure':failure},'success'
