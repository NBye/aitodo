import os,json
from openai import OpenAI

from src.utils.Datetime import Datetime
from src.utils.errors import CodeError
from src.utils.funcs import async_exec

import config


async def generate(model,prompt=None,messages=[],images=None, stream=False, suffix=None,organization=None,user=None,**options):
    nvidia                             = organization.settings.get('nvidia',{'enable':False})
    if not nvidia.get('enable'):
        raise CodeError('其他大模型')
    client                              = OpenAI(
        api_key                         = nvidia['api_key'], 
        base_url                        = "https://integrate.api.nvidia.com/v1", 
    )
    data                                = {
        'messages'                      : [],
        'model'                         : model,
        'stream'                        : stream,
    }
    # if options.get('num_ctx'):
    #     data['max_completion_tokens']   = options.get('num_ctx')
    if options.get('temperature'):
        data['temperature']   = options.get('temperature')
    if stream:
        data['stream_options']          = {"include_usage": True}
    if prompt:
        data['messages'].append({
            "role"                      : 'user',
            "content"                   : prompt if not images else [
                {"type": "input_text","text": prompt},
                *images,
            ],
            "completed"                 : Datetime.afrom().format(),
            "name"                      : '',
            "user_id"                   : ''
        })
    for i,message in enumerate(messages):
        utext,stext                     = await message.embedded(user)
        images                          = []
        for f in message.get('files',[]):
            if f.is_image():
                images.append({
                    "type"              : "input_image",
                    "image_url"         : {"url": await f.http_url()}
                })
        m                               = {
            "role"                      : message['role'],
            "content"                   : utext if not images else [
                {"type": "text","text": utext},
                *images,
            ],
            "completed"                 : message.get('completed',''),
            "name"                      : message.get('user_nickname',''),
            "user_id"                   : message.get('user_id','')
        }
        # print(json.dumps(m,indent=4, ensure_ascii=False))
        data['messages'].append(m)
        if stext:
            data['messages'].append({'role':'system','content':stext})
    # print(json.dumps(data,indent=4, ensure_ascii=False))
    completion                      = await async_exec(client.chat.completions.create,**data)
    if stream:
        for chunk in completion:
            data                    = json.loads(chunk.model_dump_json())
            # print(json.dumps(data,indent=4, ensure_ascii=False))
            if len(data['choices']) > 0:
                yield {
                    "role"     : data['choices'][0]['delta']['role'] or 'assistant',
                    "status"   : "in_progress", #'in_progress','incomplete','completed'
                    "content"  : data['choices'][0]['delta']['content'] or '',
                    "tokens"   : data['usage']['completion_tokens'] if data['usage'] else 0 #回答token数
                }, 0 #问题token数
            elif data['usage']:
                yield {
                    "role"     : 'assistant',
                    "status"   : "completed", #'in_progress','incomplete','completed'
                    "content"  : '',
                    "tokens"   : data['usage']['completion_tokens'] or 0 #回答token数
                }, data['usage']['prompt_tokens'] or 0 #问题token数
    else:
        data                        = json.loads(completion.model_dump_json())
        # print(json.dumps(data,indent=4, ensure_ascii=False))
        #返回新消息的数据，以及问题token数
        yield {
            "role"     : data['choices'][0]['message']['role'],
            "status"   : "completed", #'in_progress','incomplete','completed'
            "content"  : data['choices'][0]['message']['content'] or '',
            "tokens"   : data['usage']['completion_tokens'] #回答token数
        }, data['usage']['prompt_tokens'] #问题token数