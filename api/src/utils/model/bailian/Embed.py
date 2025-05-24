import json,random
from openai import OpenAI
import config

from src.utils.errors import CodeError
from src.utils.funcs import async_exec

async def embed(model,text,organization=None,**data):
    bailian                             = organization.settings.get('bailian',{'enable':False})
    if not bailian.get('enable'):
        raise CodeError('阿里百炼未启用')
    client                              = OpenAI(
        api_key                         = bailian['api_key'], 
        base_url                        = "https://dashscope.aliyuncs.com/compatible-mode/v1", 
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
    