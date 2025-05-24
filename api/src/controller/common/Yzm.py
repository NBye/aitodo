from captcha.image import ImageCaptcha
import base64
from io import BytesIO

from datetime import datetime

import random, string, uuid

from src.entity.ECache import ECache
from src.super.controllers import BaseController

from src.utils.errors import CodeError
from src.utils.Sms import Sms
from src.utils.Email import Email

import config

class Yzm(BaseController):
    
    async def image(self):
        post                            = await self.get_post()
        width                           = int(post.get('width') or 280)
        height                          = int(post.get('height') or 90)
        length                          = int(post.get('length') or 4)
        size                            = int(post.get('size') or 64)
        bgcolor                         = (post.get('bgcolor') or '#FFFFFF').lstrip('#')
        background_color                = tuple(int(bgcolor[i:i+2], 16) for i in (0, 2, 4))
        img_code                        = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=int(length)))
        img_code_id                     = str(uuid.uuid4())
        image                           = ImageCaptcha(width=width, height=height,font_sizes=(size,))
        img                             = image.generate_image(img_code)
        buffered                        = BytesIO()
        img.save(buffered, format="PNG")
        img_data                        = base64.b64encode(buffered.getvalue()).decode('utf-8')
        await ECache.setData(img_code_id,300,code=img_code)
        img_url                         = f"data:image/png;base64,{img_data}"
        return {'img_code_id':img_code_id,'img_code_url':img_url},'该验证码5分钟后失效'

    async def phone(self):
        post                            = await self.get_post()
        phone                           = post.get('phone')
        img_code_id                     = post.get('img_code_id')
        img_code                        = post.get('img_code','').upper()
        img_code_cache                  = await ECache.getOnceData(img_code_id,'code')
        if img_code_cache!=img_code:
            raise CodeError('图片验证码错误')
        phone_code                      = str(random.randint(100000, 999999))
        phone_code_id                   = str(uuid.uuid4())
        data                            = await Sms().send(phone,config.TENCENT_SMS_LOGIN_TEMPLATEID,[str(phone_code),'5'])
        await ECache.setData(phone_code_id,300,code=phone_code,phone=phone)
        return dict({'phone_code_id':phone_code_id},**data),'验证码发送成功'

    async def email(self):
        post                            = await self.get_post()
        email                           = post.get('email')
        img_code_id                     = post.get('img_code_id')
        img_code                        = post.get('img_code','').upper()
        img_code_cache                  = await ECache.getOnceData(img_code_id,'code')
        if img_code_cache!=img_code:
            raise CodeError('图片验证码错误')
        email_code                      = str(random.randint(100000, 999999))
        email_code_id                   = str(uuid.uuid4())
        time                            = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject                         = f'验证码: {email_code} ，该验证码5分钟后过期'
        body                            = f'<p>验证码: {email_code} ，发送时间: {time} ，该验证码5分钟后过期。</p>'
        await Email().send(email, subject, body)
        await ECache.setData(email_code_id,300,code=email_code,email=email)
        return {'email_code_id':email_code_id},'验证码发送成功'