import os,json,re,random,traceback,asyncio
from openai import OpenAI
from ragflow_sdk import RAGFlow

from src.utils.funcs import log,async_exec
from src.entity.EChatMessage import EChatMessage
from src.entity.EOrganization import EOrganization
from src.entity.EUser import EUser
import config

async def send(model:str,messages:list[EChatMessage],organization:EOrganization,user:EUser,tools:list=[], stream:bool=True,**options):
    ragflow                             = organization.settings.get('ragflow',{'enable':False})
    if not ragflow.get('enable'):
        raise CodeError('其他大模型')
    host                                = ragflow.get('host') or ''
    api_key                             = ragflow.get('api_key') or ''

    rag_object                          = RAGFlow(
        api_key                         = api_key, 
        base_url                        = host
    )
    assistant                           = None
    try:
        assistants                      = rag_object.list_chats(name=user.nickname)
        for s in assistants:
            if s.name == user.nickname:
                assistant               = s
                break
        if not assistant:
            raise Exception(f'createing assistant {user.nickname}')
    except Exception:  
        datasets                        = rag_object.list_datasets()
        # dataset_ids                     = [dataset.id for dataset in datasets]
        assistant                       = rag_object.create_chat(
            user.nickname, 
            avatar                      = config.HOST + user.avatar, 
            # dataset_ids                 = dataset_ids
        )
    chat_id                             = assistant.id
    client                              = OpenAI(
        api_key                         = api_key,
        base_url                        = f'{host}/api/v1/chats_openai/{chat_id}'
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
    for i,message in enumerate(messages):
        utext,stext                     = await message.embedded(user)
        if stext:
            data['messages'].append({'role':'system','content':stext})
        images,audios,videos            = [],[],[]
        for f in message.get('files',[]):
            utext                       += '\n\n'+ await f.to_string()
        m                               = {
            "role"                      : message['role'],
            "content"                   : utext,
        }
        if m['content']:
            # print(json.dumps(m,indent=4, ensure_ascii=False))
            data['messages'].append(m)
    # print('<' * 50)
    # print(json.dumps(data,indent=4, ensure_ascii=False))
    # print('>' * 50)
    total_prompt_tokens                 = 0
    total_output_tokens                 = 0
    tasks                               = {}
    completion                          = await async_exec(client.chat.completions.create,**data)
    if stream:
        for chunk in completion:
            data                        = json.loads(chunk.model_dump_json())
            # print(json.dumps(data,indent=4, ensure_ascii=False))
            for choice in data['choices']:
                message                 = choice['delta']
                content                 = message.get('content','') or ''
                parse_calld(message,tasks)
                for char in content:
                    yield {
                        "role"  : message['role'],
                        "content": char,
                        "tokens": 0,
                        "status": "in_progress",
                    }, 0 
                    await asyncio.sleep(0.01)
            if data['usage']:
                total_prompt_tokens     = data['usage']['prompt_tokens']
                total_output_tokens     = data['usage']['completion_tokens']
    else:
        data                            = json.loads(completion.model_dump_json())
        # print(json.dumps(data,indent=4, ensure_ascii=False),'\n-------------------')
        total_prompt_tokens             = data['usage']['prompt_tokens']
        total_output_tokens             = data['usage']['completion_tokens']
        for choice in data['choices']:
            message                     = choice['message'] 
            parse_calld(message,tasks)
            yield {
                "status"                : 'in_progress',
                "role"                  : message['role'],
                "content"               : message['content'],
                "tokens"                : 0
            }, 0
    yield {
        "status"                        : 'completed',
        "role"                          : 'assistant',
        "content"                       : '',
        "tokens"                        : total_output_tokens,
        "tool_calls"                    : [(t[0],json.loads(t[1]) if isinstance(t[1],str) else t[1]) for t in tasks.values()]
    }, total_prompt_tokens
    
def parse_calld(message,tasks):
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
                log('Model ragflow parse_calld Error:'+ json.dumps(tool,ensure_ascii=False))
        else:
            tasks[index]                = [name,arguments]
