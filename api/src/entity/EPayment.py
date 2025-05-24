from __future__ import annotations
from src.super.ESModel import ESModel

from src.utils.U62Id import U62Id
from src.utils.funcs import md5
from src.utils.errors import CodeError

import time,httpx
import config

class EPayment(ESModel):

    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
       "completed"                      : None,
       "status"                         : 'paying',
       "data"                           : {},
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
                "organization_id"       : {"type": "keyword"}, 

                "trade_no"              : {"type": "keyword"},      #上游贸易单号
                "amount"                : {"type": "float"},        #支付金额
                "remark"                : {"type": "text"},         #备注
                "status"                : {"type": "keyword"},      #支付状态 paying,fail,success
                "status_description"    : {"type": "text"},         #状态描述
                "scene"                 : {"type": "keyword"},      #场景 recharge|consume|commission
                "data"                  : {"type": "object","enabled": False}, # 拓展的其他数据

                "completed"             : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    async def pay(self,**data):
        accountid                       = config.PAY_ACCOUNT_ID
        secret_key                      = config.PAY_SECRET_KEY
        merchant_id                     = config.PAY_MERCHANT_ID
        randstr                         = U62Id.generate(8)
        timestamp                       = str(int(time.time()))
        data['merchant_id']             = merchant_id
        data['amount']                  = round(self.amount, 2)
        data['remark']                  = self.remark
        data['client_trade_no']         = self._id
        data['notify_url']              = f'{config.HOST}/notify/pay/recharge'
        # data['product_list']            = data.get('product_list',None) or [
        #                                     {
        #                                         "id"        : 1,
        #                                         "name"      : self.remark,
        #                                         "quantity"  : 1,
        #                                         "price"     : self.amount
        #                                     }
        #                                 ]
        headers                         = {
            'accountid'                 : accountid,
            'timestamp'                 : timestamp,
            'randstr'                   : randstr,
            'sign'                      : self.to_sign(data,accountid,secret_key,randstr,timestamp),
        }
        async with httpx.AsyncClient() as client:
            response                    = await client.post(config.PAY_HOST + "/open/order/makePayUrl", json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise CodeError(f'Pay response error:{response.status_code} \n{response.text}')


    def to_sign(self,data:dict,accountid,secret_key,randstr,timestamp):
        '''
        foreach ($request->post() as $k => $v) {
            if ($v !== null && $v !== ''  && $v !== null && !is_array($v)) {
                $sign_arr[]             = "$k=$v";
            }
        }
        sort($sign_arr);
        if (md5(implode('&', $sign_arr) . $secret_key) != $_sign) {
            $this->error("验签失败");
        }
        '''
        sign_arr                        = [
            f'timestamp={timestamp}',
            f'randstr={randstr}',
        ]
        for k,v in data.items():
            if isinstance(v,float):
                v                       = str(int(v)) if v.is_integer() else str(v)
                sign_arr.append(f'{k}={v}')
            elif v!=None and v!='' and not isinstance(v, (dict,list,set,tuple)):
                sign_arr.append(f'{k}={v}')
        sign_arr                        = sorted(sign_arr)
        return md5('&'.join(sign_arr)+secret_key)