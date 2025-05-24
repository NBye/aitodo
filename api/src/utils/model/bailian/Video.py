import os,random,httpx
import dashscope
from http import HTTPStatus
from dashscope import VideoSynthesis

from datetime import datetime

from src.entity.EFile import EFile 
from src.entity.EDataBase import EDataBase 
from src.utils.errors import CodeError 

import config

async def from_text(model,prompt,name=None,duration=5,width=1280,height=720,organization=None,user=None):
    if int(duration)>5:
        raise CodeError('不能超过5s')
    if not organization:
        raise CodeError(f'组织未开通:阿里百炼')
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    rsp                                 = VideoSynthesis.call(
        api_key                         = bailian['api_key'],
        model                           = model,
        prompt                          = prompt,
        size                            = f'{width}*{height}',
        duration                        = duration,
    )
    if rsp.status_code == HTTPStatus.OK and rsp.output.video_url:
        async with httpx.AsyncClient() as client:
            response                    = await client.get(rsp.output.video_url)
            if response.status_code == 200:
                binary                  = response.content  # 视频数据存储在变量中
            else:
                raise CodeError('下载失败，您可以自行下载。\n源地址为: '+rsp.output.video_url)
    else:
        raise CodeError('绘图失败, status_code: %s, code: %s, message: %s' % (rsp.status_code, rsp.code, rsp.message))
    if not binary:
        raise CodeError('绘图失败')
    if name:
        name                            = name.split('.')[0]+'.mp4'
    else:
        name                            = '图生视频' + datetime.now().strftime("%Y%m%d%H%M%S") + '.mp4'
    return await EFile.upload_binary(
        binary                          = binary,
        name                            = name,
        location                        = 'public',
        user                            = user,
        organization                    = organization,
        remark                          = 'requestId:' + rsp.request_id
    )

async def from_image(model,prompt,file_id=None,name=None,duration=5,efile=None,organization=None,user=None):
    if int(duration)>5:
        raise CodeError('不能超过5s')
    if not organization:
        raise CodeError(f'组织未开通:阿里百炼')
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    if file_id:
        efile                           = await EFile.afrom(_id=file_id)
    if not efile:
        raise CodeError('未指定有效的文件')
    img_url                             = await efile.temp_url()
    rsp                                 = VideoSynthesis.call(
        api_key                         = bailian['api_key'],
        model                           = model,
        prompt                          = prompt,
        img_url                         = await efile.temp_url(),
        parameters                      = {
            "duration"                  : duration,
        }
    )
    if rsp.status_code == HTTPStatus.OK and rsp.output.video_url:
        async with httpx.AsyncClient() as client:
            response                    = await client.get(rsp.output.video_url)
            if response.status_code == 200:
                binary                  = response.content  # 视频数据存储在变量中
            else:
                raise CodeError('下载失败，您可以自行下载。\n源地址为: '+rsp.output.video_url)
    else:
        raise CodeError('绘图失败, status_code: %s, code: %s, message: %s' % (rsp.status_code, rsp.code, rsp.message))
    if not binary:
        raise CodeError('绘图失败')
    if name:
        name                            = name.split('.')[0]+'.mp4'
    else:
        name                            = '图生视频' + datetime.now().strftime("%Y%m%d%H%M%S") + '.mp4'
    return await EFile.upload_binary(
        binary                          = binary,
        name                            = name,
        location                        = 'public',
        user                            = user,
        organization                    = organization,
        remark                          = 'requestId:' + rsp.request_id
    )
