import json,random
from openai import OpenAI
import config

from src.utils.errors import CodeError
from src.utils.funcs import async_exec

async def embed(model,text,organization=None,**data):
    other                             = organization.settings.get('other',{'enable':False})
    if not other.get('enable'):
        raise CodeError('其他大模型')
    client                              = OpenAI(
        api_key                         = other['api_key'], 
        base_url                        = other['base_url'], 
    )
    completion                          = await async_exec(
        client.embeddings.create,
        model                           = model,
        input                           = text,
        dimensions                      = 1024,
        encoding_format                 = "float"
    )
    data                                = completion.model_dump_json()
    data                                = json.loads(data)
    embedding                           = data['data'][0]['embedding']
    prompt_tokens                       = data['usage']['prompt_tokens']
    total_tokens                        = data['usage']['total_tokens']
    return embedding,total_tokens
    