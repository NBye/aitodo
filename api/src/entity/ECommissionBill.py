from __future__ import annotations
from src.super.ESModel import ESModel

from src.utils.U62Id import U62Id
from src.utils.funcs import md5
from src.utils.errors import CodeError

from src.entity.EPayment import EPayment

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import time,re
import config

class ECommissionBill(ESModel):

    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
       "status"                         : 'unsettled'
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

                "month"                 : {"type": "date","format": "yyyy-MM"},      # 月份 yyyy-mm
                "amount"                : {"type": "float"},        # 结算金额
                "remark"                : {"type": "text"},         # 备注
                "status"                : {"type": "keyword"},      # 结算章台 unsettled,settled

                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    async def refresh(cls,organization_id=None,month=None):
        if month and re.match(r"^\d{4}-\d{2}$", month):
            now                         = datetime.strptime(month, "%Y-%m")
        if month and re.match(r"^\d{6}$", month):
            now                         = datetime.strptime(month, "%Y%m")
        else:
            now                         = datetime.now()
        stime                           = (now).strftime("%Y-%m-01 00:00:00")
        etime                           = (now + relativedelta(months=1)).strftime("%Y-%m-01 00:00:00")
        month                           = now.strftime("%Y-%m")
        query                           = {"bool": {"must": [
            {"term" :{"status": 'success'}},
            {"term" :{"scene": 'commission'}},
            {'range':{"completed":{"gte": stime,"lt": etime}}},
        ]}}
        if organization_id:
            query['bool']['must'].append({"term": {"organization_id": organization_id}})
        aggs                            = await EPayment.aggs({
            "organizations": {
                "terms"                 : {
                    "field"             : "organization_id",
                    "size"              : 1000,
                },
                "aggs": {
                    "total_amount"      : {
                        "sum"           : {
                            "field"     : "amount"
                        }
                    }
                }
            }
        
        },query=query)
        total                           = 0
        for item in aggs['organizations']['buckets']:
            organization_id             = item['key']
            amount                      = round(item['total_amount']['value'],2)
            bill                        = await cls.afrom(organization_id=organization_id,month=month)
            if bill:
                await bill.upset(amount=amount)
            else:
                bill                    = await cls.create(
                    organization_id     = organization_id,
                    month               = month,
                    amount              = amount,
                    remark              = f'{month}佣金账单',
                )
            total                       += 1
        await cls.refreshIndex()
        return total,month