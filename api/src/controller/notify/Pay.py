import json
from quart import request
from src.super.controllers import BaseController
from src.utils.errors import CodeError
from datetime import datetime

from src.entity.EPayment import EPayment
import config


class Pay(BaseController):

    async def recharge(self):
        post                            = await self.get_post()
        order_client_trade_no           = post.get('order_client_trade_no')
        order_status                    = int(post.get('order_status'))
        payment                         = await EPayment.afrom(
            _id                         = order_client_trade_no,
        )
        completed                       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if payment.status != 'paying':
            return {}, f'Error:current status {payment.status}!'
        secret_key                      = config.PAY_SECRET_KEY
        sign                            = request.headers.get('sign')
        accountid                       = request.headers.get('accountid')
        randstr                         = request.headers.get('randstr')
        timestamp                       = request.headers.get('timestamp')
        sign2                           = payment.to_sign(post,accountid,secret_key,randstr,timestamp)
        if sign2 != sign:
            return {},f'final: {sign2}!={sign}'
        if order_status == 1:
            # 组织储值
            if payment.organization_id:
                from src.entity.EOrganization import EOrganization
                organization            = await EOrganization.afrom(_id=payment.organization_id)
                if organization:
                    after               = await organization.inc_balance(payment.amount)
                    before              = round(after+payment.amount,2)
            # 用户储值
            elif payment.user_id:
                from src.entity.EUser import EUser
                user                    = await EUser.afrom(_id=payment.user_id)
                if user:
                    before              = user.balance
                    after               = before + payment.amount
                    await user.upset(refresh=True,balance=after)
            else:
                return {},'Error: Lack of main body !'
            await payment.upset(status='success',completed=completed,data={'before':before,'after':after})
        elif order_status != 0:
            await payment.upset(status='fail',completed=completed)
        return {},'success'
