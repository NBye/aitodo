import random
from src.super.controllers import BaseController


class Email(BaseController):
    async def search(self):
        post                            = await self.get_post()
        keyword                         = post.get('keyword')
        return {"list":[
            {"id":"10000","title":f"你好,合作愉快 {keyword}"},
            {"id":"10001","title":f"{keyword} 关于短信余额不足"},
        ]},

    async def info(self):
        post                            = await self.get_post()
        id                              = str(post.get('id'))
        if id == '10000':
            return {"id":id,"title":f"你好啊","body":f"跟你合作真实愉快,优惠大酬宾25年1月送10000元优惠券尽快领取。"}
        if id == '10001':
            return {"id":id,"title":f"你好啊，关于短信余额不足","body":f"您的短信剩余39条，已不足，请尽快充值。"}
        else:
            return {},'找不到',401

    async def send(self):
        post                            = await self.get_post()
        id                              = post.get('id')
        body                            = post.get('body')
        a = random.randint(0,1)
        if a==1:
            return {},f'回复{id}成功: {body}'
        else:
            return {},f'回复{id}失败！'