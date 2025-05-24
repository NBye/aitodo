import os,json,httpx,types,re,asyncio

from src.utils.Datetime import Datetime
from src.utils.errors import CodeError
from src.utils.funcs import log

import config

async def send(model, messages, tools=[], stream=True,organization=None,user=None,**options):
    headers                             = {
        "Content-Type"                  : "application/json",
    }
    ollama                              = organization.settings.get('ollama',{'enable':False})
    if not ollama.get('enable'):
        raise CodeError('Ollama未启用')
    if ollama.get('username',None) and ollama.get('password',None):
        auth                            = (ollama['username'],ollama['password'])
    else:
        auth                            = None
    if ollama.get('apikey',None):
        headers['Authorization']        = f'Bearer {ollama["apikey"]}'
    data                                = {
        'messages'                      : [],
        'tools'                         : tools,
        'model'                         : model,
        'stream'                        : stream,
        'options'                       : options
    }
    ln                                  = len(messages)
    for i,message in enumerate(messages):
        utext,stext                     = await message.embedded(user)
        if stext:
            data['messages'].append({'role':'system','content':stext})
        images,audios,videos            = [],[],[]
        for f in message.get('files',[]):
            if f.is_image():
                mime,base64_data        = await f.base64_data()
                if base64_data:
                    images.append(base64_data)
            else: 
                utext                   += '\n\n'+ await f.to_string()
        m                               = {
            "role"                      : message['role'],
            "content"                   : utext,
            "images"                    : None if not images else images,
        }
        data['messages'].append(m)
    async with httpx.AsyncClient() as client:
        response                        = await client.post(ollama['host'] + "/api/chat", json=data, headers=headers, auth=auth, timeout=300)
        if response.status_code != 200:
            raise CodeError(f'ollama response error:{response.status_code} {response.text}')
        tasks                           = {}
        if stream:
            token_total                 = 0
            for chunk in response.iter_lines():
                if not chunk:
                    continue
                data                    = json.loads(chunk)
                token_total             += data.get('eval_count',0)
                if token_total > 10000:
                    raise CodeError('生成中断,超出最大tokn 10000 限制')
                parse_calld(data['message'],tasks)
                role                    = data['message']['role'] or 'assistant'
                content                 = data['message']['content'] or ''
                if data['done'] == False:
                    yield {
                        "role"          : role,
                        "content"       : content,
                        "tokens"        : 0, #回答token数
                        "status"        : "in_progress", #'in_progress','incomplete','completed',
                    }, 0 #问题token数
                else:
                    if not tasks and tools:
                        for char in content:
                            yield {
                                "role"  : role,
                                "content": char,
                                "tokens": data['eval_count'] or 0,
                                "status": "in_progress",
                            }, 0 
                            await asyncio.sleep(0.02)
                    yield {
                        "role"          : role,
                        "content"       : '',
                        "tokens"        : 0,
                        "status"        : "completed",
                        "tool_calls"    : [(t[0],json.loads(t[1]) if isinstance(t[1],str) else t[1]) for t in tasks.values()]
                    }, data.get('prompt_eval_count',0) 
        else:
            data                        = response.json()
            parse_calld(data['message'],tasks)
            yield {
                "role"          : data['message']['role'] or 'assistant',
                "status"        : "completed",
                "content"       : data['message']['content'],
                "tokens"        : data.get('eval_count',0),
                "tool_calls"    : [(t[0],json.loads(t[1]) if isinstance(t[1],str) else t[1]) for t in tasks.values()]
            }, data.get('prompt_eval_count',0)

    

def parse_calld(message,tasks):
    for tool in (message.get('tool_calls') or []):
        index                           = str(tool.get('index') or 0)
        tasks[index]                    = (
            tool['function']['name'],
            tool['function']['arguments']
        )
