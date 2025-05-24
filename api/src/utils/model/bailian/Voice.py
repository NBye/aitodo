import os,random,json
import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
from datetime import datetime

from src.entity.EFile import EFile 
from src.entity.EDataBase import EDataBase 
from src.utils.errors import CodeError 
from src.utils.funcs import async_exec

import config

async def clone(model,url=None,file_id=None,organization=None,user=None):
    if not organization:
        raise CodeError(f'组织未开通:阿里百炼')
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    dashscope.api_key                   = bailian['api_key']
    # 创建语音注册服务实例
    service                             = VoiceEnrollmentService()
    # 调用create_voice方法复刻声音，并生成voice_id
    if not url and file_id:
        efile                           = await EFile.afrom(_id=file_id)
        if not efile:
            raise CodeError('找不到克隆的音频文件')
        url                             = await efile.temp_url()
    voice_id                            = await async_exec(
        service.create_voice,
        target_model                    = model, 
        prefix                          = 'p1', 
        url                             = url
    )
    if user:
        remark                          = '语音复刻'+user.nickname
    else:
        remark                          = '语音复刻'
    data                                = await EDataBase.create(
        organization                    = organization,
        user                            = user,
        type                            = 'voice_clone',
        remark                          = remark,
        content                         = {
            'model'                     : ['bailian',model],
            'voice_id'                  : voice_id,
            'keyindex'                  : 0,
            'requestId'                 : service.get_last_request_id(),
        }
    )
    return data

async def create(model,clone_id,text,name=None,organization=None,user=None,keyindex=None):
    if not organization:
        raise CodeError(f'组织未开通:阿里百炼')
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    dashscope.api_key                   = bailian['api_key']
    data                                = await EDataBase.afrom(_id=clone_id)
    if not data:
        raise CodeError('请指定复刻id，或从新复刻音频。')
    data                                = json.loads(data.content)
    voice_id                            = data['voice_id']
    synthesizer                         = await async_exec(
        SpeechSynthesizer,
        model                           = model, 
        voice                           = voice_id
    )
    audio                               = synthesizer.call(text)
    if not audio:
        raise CodeError('合成语音失败')
    if name:
        name                            = name.split('.')[0]+'.mp3'
    else:
        name                            = '合成语音' + datetime.now().strftime("%Y%m%d%H%M%S") + '.mp3'
    return await EFile.upload_binary(
        binary                          = audio,
        name                            = name,
        location                        = 'public',
        user                            = user,
        organization                    = organization,
        remark                          = 'requestId:' + synthesizer.get_last_request_id()
    )
