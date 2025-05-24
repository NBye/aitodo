import os,random,httpx
import dashscope
from dashscope import ImageSynthesis
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

from datetime import datetime

from src.entity.EFile import EFile 
from src.entity.EDataBase import EDataBase 
from src.utils.errors import CodeError 

import config

async def from_text(model,prompt,name:str=None,width:int=800,height:int=600,n:int=1,organization=None,user=None):
    if n>4:
        raise CodeError('不能超过4张图片')
    if width > 1440:
        width                           = 1440
    if height > 1440:
        height                          = 1440
    if not organization:
        raise CodeError(f'组织未开通:阿里百炼')
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    rsp                                 = ImageSynthesis.call(api_key=bailian['api_key'],
        model                           = model,
        prompt                          = prompt,
        n                               = n,
        size                            = f'{width}*{height}'
    )
    files                               = []
    if rsp.status_code == HTTPStatus.OK:
        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            async with httpx.AsyncClient() as client:
                response                = await client.get(result.url)
                files.append(await EFile.upload_binary(
                    binary              = response.content,
                    name                = file_name,
                    location            = 'public',
                    user                = user,
                    organization        = organization,
                    remark              = 'requestId:' + rsp.request_id
                ))
    return files
    
