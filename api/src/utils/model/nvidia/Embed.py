import json,random
from openai import OpenAI
import config

from src.utils.errors import CodeError
from src.utils.funcs import async_exec

async def embed(model,text,organization=None,**data):
    nvidia                             = organization.settings.get('nvidia',{'enable':False})
    if not nvidia.get('enable'):
        raise CodeError('其他大模型')
    client                              = OpenAI(
        api_key                         = nvidia['api_key'], 
        base_url                        = "https://integrate.api.nvidia.com/v1", 
    )
    completion                          = await async_exec(
        client.embeddings.create,
        model                           = model,
        input                           = text,
        # dimensions                      = 1024,
        encoding_format                 = "float"
    )
    data                                = completion.model_dump_json()
    data                                = json.loads(data)
    embedding                           = data['data'][0]['embedding']
    enbedding                           = (embedding + [0] * 1024)[:1024]
    prompt_tokens                       = data['usage']['prompt_tokens']
    total_tokens                        = data['usage']['total_tokens']
    return embedding,total_tokens
    