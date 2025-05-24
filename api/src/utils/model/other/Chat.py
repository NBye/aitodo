import os,json,re,random,traceback
from openai import OpenAI

from src.utils.funcs import log,async_exec
from src.entity.EChatMessage import EChatMessage
from src.entity.EOrganization import EOrganization
from src.entity.EUser import EUser

async def send(model:str,messages:list[EChatMessage],organization:EOrganization,user:EUser,tools:list=[], stream:bool=True,**options):
    other                               = organization.settings.get('other',{'enable':False})
    if not other.get('enable'):
        raise CodeError('其他大模型')
    client                              = OpenAI(
        api_key                         = other['api_key'], 
        base_url                        = other['base_url'], 
    )
    data                                = {
        'messages'                      : [],
        'model'                         : model,
        'stream'                        : stream,
    }
    if options.get('temperature'):
        data['temperature']             = options.get('temperature')
    if len(tools):
        data['tools']                   = tools
    if stream:
        data['stream_options']          = {"include_usage": True}
    for i,message in enumerate(messages):
        utext,stext                     = await message.embedded(user)
        if stext:
            data['messages'].append({'role':'system','content':stext})
        images,audios,videos            = [],[],[]
        for f in message.get('files',[]):
            if f.is_image():            # 图片载入
                images.append({
                    "type"              : "image_url",
                    "image_url"         : {"url":await f.temp_url()}
                })
            elif f.is_audio():            # 音频载入
                audios.append({
                    "type"              : "input_audio",
                    "input_audio"       : {
                        "data"          : {"url":await f.temp_url()},
                        "format"        : f.type,
                    },
                }),
            # elif f.is_video():            # 视频载入
            #     pass
            else: 
                utext                   += '\n\n'+ await f.to_string()
        m                               = {
            "role"                      : message['role'],
            "content"                   :  [
                *images,*audios,*videos,
                *([{"type": "text","text": utext}] if utext else [])
            ],
        }
        if m['content']:
            # print(json.dumps(m,indent=4, ensure_ascii=False))
            data['messages'].append(m)
    # print('<' * 50)
    # print(json.dumps([m for m in data['messages']],indent=4, ensure_ascii=False))
    # print('>' * 50)
    total_prompt_tokens                 = 0
    total_output_tokens                 = 0
    tasks                               = {}
    try:
        completion                      = await async_exec(client.chat.completions.create,**data)
        if stream:
            for chunk in completion:
                data                    = json.loads(chunk.model_dump_json())
                # print(json.dumps(data,indent=4, ensure_ascii=False))
                for choice in data['choices']:
                    message             = choice['delta']
                    await parse_calld(message,tasks)
                    if message['content']:
                        yield {
                            "status"    : 'in_progress',                    #'in_progress','incomplete','completed'
                            "role"      : message['role'],
                            "content"   : message['content'],
                            "tokens"    : 0 # 输出token数
                        }, 0                    # 问题token数
                if data['usage']:
                    total_prompt_tokens = data['usage']['prompt_tokens']
                    total_output_tokens = data['usage']['completion_tokens']
        else:
            data                        = json.loads(completion.model_dump_json())
            # print(json.dumps(data,indent=4, ensure_ascii=False),'\n-------------------')
            total_prompt_tokens         = data['usage']['prompt_tokens']
            total_output_tokens         = data['usage']['completion_tokens']
            for choice in data['choices']:
                message                 = choice['message'] 
                await parse_calld(message,tasks)
                yield {
                    "status"            : 'in_progress',
                    "role"              : message['role'],
                    "content"           : message['content'],
                    "tokens"            : 0
                }, 0
        yield {
            "status"                    : 'completed',
            "role"                      : 'assistant',
            "content"                   : '',
            "tokens"                    : total_output_tokens,
            "tool_calls"                : [(t[0],json.loads(t[1]) if isinstance(t[1],str) else t[1]) for t in tasks.values()]
        }, total_prompt_tokens
    except BaseException as e:
        yield {
            "status"                    : 'incomplete',
            "role"                      : 'assistant',
            "content"                   : f'```\n{str(e)}\n{traceback.format_exc()}\n```',
            "tokens"                    : total_output_tokens,
            "tool_calls"                : [(t[0],json.loads(t[1]) if isinstance(t[1],str) else t[1]) for t in tasks.values()]
        }, total_prompt_tokens

    
async def parse_calld(message,tasks):
    for tool in (message.get('tool_calls') or []):
        index                           = str(tool['index'])
        name                            = tool['function']['name']
        arguments                       = tool['function']['arguments']
        if index in tasks:
            if isinstance(arguments,dict):
                tasks[index][1]         = arguments
            elif isinstance(arguments,str):
                tasks[index][1]        += arguments
            elif arguments:
                await log('Model other parse_calld Error:'+ json.dumps(tool,ensure_ascii=False))
        else:
            tasks[index]                = [name,arguments]
