import json
import httpx
import config
from src.utils.errors import CodeError

async def embed(model,text,organization=None,**data):
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
        "model"                         : model,
        "input"                         : text
    }
    async with httpx.AsyncClient() as client:
        response                        = await client.post(ollama['host'] + "/api/embed", json=data, headers=headers, auth=auth)
        data                            = response.json()
        # data["total_duration"]    #: 14143917, 生成响应的总时间
        # data["load_duration"]     #: 1019500,  加载模型时间
        # data["prompt_eval_count"] #: 8 令牌数量
        if data.get('embeddings')==None:
            return None,0
        else:
            return data['embeddings'][0],data["prompt_eval_count"]