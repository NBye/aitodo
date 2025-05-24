
import re
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, select_autoescape,FileSystemLoader

from src.utils.CDict import CDict


env = Environment(
    autoescape                          = select_autoescape(),
    trim_blocks                         = True,
    enable_async                        = True
)

async def File(file_id):
    from src.entity.EFile import EFile
    return await EFile.afrom(_id=file_id)

async def file_content(file):
    agent                               = Agent.init(user=None,file_id=self.file._id,**self.file)
    await agent.execute()
    return agent.content

async def http_url(file):
    return await file.http_url()
async def temp_url(file,seconds=1800):
    return await file.temp_url(seconds)


def merge(*dicts):
    merged                              = {}
    for data in dicts:
        if isinstance(data, dict): 
            merged.update(data)
    return merged

def regex(value, pattern):
    return bool(re.match(pattern, value))

def indent(text,indent=1,chr='    '):
    paragraphs                          = text.split("\n")
    indented_paragraphs                 = [(chr * indent) + paragraph if paragraph.strip() else "" for paragraph in paragraphs]
    return "\n".join(indented_paragraphs)

def replace(content,pattern,text='',flags=re.DOTALL,**args):
    return re.sub(pattern, text, content, flags=flags,**args)

def date(value, format="%Y-%m-%d %H:%M:%S"):
    if value=='now':
        dt                              = datetime.now()
    elif isinstance(value, (int, float)):
        dt                              = datetime.fromtimestamp(value)
    elif isinstance(value, str):
        if value.strip().startswith('+') or value.strip().startswith('-'):
            dt                          = datetime.now() + parse_offset(value)
        else:
            dt                          = parser.parse(value)
    elif isinstance(value, datetime):
        dt                              = value
    else:
        raise ValueError("Unsupported input type")
    return dt.strftime(format)


async def File(file_id):
    from src.entity.EFile import EFile
    return await EFile.afrom(_id=file_id)

async def get_content(file):
    agent                               = Agent.init(user=None,file_id=self.file._id,**self.file)
    await agent.execute()
    return agent.content

async def http_url(file):
    return await file.http_url()
async def temp_url(file,seconds=1800):
    return await file.temp_url(seconds)

env.filters["File"]                     = File
env.filters["get_content"]              = get_content
env.filters["http_url"]                 = http_url
env.filters["temp_url"]                 = temp_url

env.filters["merge"]                    = merge
env.filters["regex"]                    = regex
env.filters["indent"]                   = indent
env.filters["replace"]                  = replace
env.filters["date"]                     = date


async def Template(template,strict=True,**data):
    try:
        template                        = env.from_string(template)
        return (await template.render_async(**data)).strip()
    except BaseException as e:
        if strict:
            raise e
        return f"模板解析异常: {e}"
