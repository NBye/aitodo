import os,json,httpx

from src.utils.Datetime import Datetime
from src.utils.errors import CodeError

import config


async def generate(model,prompt=None,messages=[],images=None, stream=False, suffix=None,organization=None,user=None,**options):
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
    if prompt==None: 
        prompt                          = []
        for m in messages:
            utext,stext                 = await m.embedded(user)
            prompt.append(utext)
            if stext:
                prompt.append(stext)
        prompt                          = "\n\n".join(prompt)
    data                                = {
        'model'                         : model,
        'prompt'                        : prompt,
        'images'                        : images,
        'stream'                        : stream,
        'suffix'                        : suffix,
        'options'                       : options,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(ollama['host'] + "/api/generate", json=data, headers=headers, auth=auth,timeout=300)
        if stream:
            if response.status_code == 200:
                content                     = ''
                for chunk in response.iter_lines():
                    if chunk:
                        data                = json.loads(chunk)
                        content             += data['response'] or ''
                        # print(json.dumps(data,indent=4, ensure_ascii=False))
                        if data['done'] == False:
                                yield {
                                "role"      : 'assistant',
                                "status"    : "in_progress",
                                "content"   : data['response'] or '',
                                "tokens"    : 0 
                            }, 0
                        else:
                            yield {
                                "role"      : 'assistant',
                                "status"    : "completed",
                                "content"   : data['response'] or '',
                                "tokens"    : data['eval_count'] or 0
                            }, data.get('prompt_eval_count',0)
            else:
                raise Exception(f'ollama response error:{response.status_code}')
        else:
            data                            = response.json()
            yield {
                "role"                      : 'assistant',
                "status"                    : "completed",
                "content"                   : data['response'] or '',
                "tokens"                    : data['eval_count'] or 0 #回答token数
            }, data.get('prompt_eval_count',0)

