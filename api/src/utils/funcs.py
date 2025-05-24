import os,uuid,hashlib,random,asyncio
from datetime import datetime
from src.utils.errors import CodeError
import asyncio,io
import config

import fitz,mammoth
from markdownify import markdownify as md

def wait(async_function):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_function)

async def async_exec(call_tools,*args,**keywords):
    return await asyncio.to_thread(call_tools,*args, **keywords)

async def log(text,name=None,prefix=None,end="\n",p=False):
    if p and config.QUART_ENV != 'production':
        print(text)
    if name==None:
        name                            = f'{datetime.now().strftime("%Y/%m/%d")}/{datetime.now().strftime("%H%M%S")}.{str(datetime.now().microsecond)[:3]}.log'
    else:
        name                            = f'{datetime.now().strftime("%Y/%m/%d")}/{name}'
    filpath                             = f'{config.LOG_DIR}/{name}'
    dirname                             = os.path.dirname(filpath)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with open(filpath, 'a') as file:
        if prefix==None:
            prefix                      = datetime.now().strftime('%Y-%m-%d %H:%M:%S ')
        file.write(f'{prefix}{text}{end}')
    return name

def md5(string):
    md5_hash                            = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    return md5_hash.hexdigest()

def text_indent(text,indent=1,chr='    '):
    paragraphs = text.split("\n")
    indented_paragraphs = [(chr * indent) + paragraph if paragraph.strip() else "" for paragraph in paragraphs]
    return "\n".join(indented_paragraphs)

def byteFormat(byte):
    for i,b in enumerate(['B','KB','MB','GB','TB','PB','EB','ZB','YB']):
        if byte // 1024**(i+1) == 0:
            if i==0:
                return f'{byte}{b}'
            else:
                return f'{byte / 1024 ** i :.1f}{b}'
    return '∞'

def optimized(**data):
    o                                   = {}
    for k,v in data.items():
        if v!=None:
            o[k]                        = v
    return o

def defOptimized(attrs,defset=True,**defo):
    try:
        o                               = {}
        for k,v in defo.items():
            if isinstance(v, dict) and type(v).__name__!='dict':
                o[k]                    = attrs.get(k,None)
            elif isinstance(v, dict) and isinstance(attrs.get(k,None), dict) and v:
                o[k]                    = defOptimized(attrs[k],defset,**v)
            elif attrs.get(k,None)!=None and v!=None:
                o[k]                    = type(v)(attrs[k])
            elif attrs.get(k,None)!=None:
                o[k]                    = attrs[k]
            elif defset:
                o[k]                    = v
        return o
    except (ValueError, TypeError) as e:
        raise CodeError(f'数据类型错误: {e}')

def generateRole():
    i                                   = random.randint(0, 49)
    sex                                 = '00100010101011001111110100011011100100101001100110'[i]
    url                                 = f'/static/avatar/{i+1}.png'
    nicknames_prefix                    = [
        "大", "小", "老", "胖", "瘦", "黑", "白", "红", "阿", "铁", 
        "金", "银", "亮", "东", "西", "南", "北", "天", "地", "云",
        "雷", "火", "水", "风", "青", "黄", "紫", "快", "慢", "新",
        "旧", "高", "矮", "长", "短", "美", "丑", "帅", "神", "圣",
        "恶", "善", "单", "双", "冬", "夏", "春", "秋", "寒", "热"
    ]
    if sex=='1':
        nicknames_middle                = [
            "虎", "狗", "猫", "狼", "龙", "牛", "马", "豹", "狮", "熊",
            "鲸", "鹰", "猴", "象", "骆驼", "骡", "鲨", "虾", "蚂蚁", "大象"
        ]
        nicknames_suffix                = [
            "哥", "爷", "叔", "王", "仔", "侠", "头", "手", "将", "军",
            "霸", "爷们", "哥们", "船长", "战士", "老板", "大佬", "国王", "强人", "大师"
        ]
    else:
        nicknames_middle                = [
            "兔", "鸟", "猫", "鱼", "羊", "鹿", "燕子", "蝴蝶", "孔雀", "麻雀",
            "鹦鹉", "燕", "鸽子", "狐狸", "松鼠", "花鹿", "梅花", "绵羊", "天鹅", "鹤"
        ]
        nicknames_suffix                = [
            "姐", "妹", "妞", "娃", "仙", "星", "宝", "仙女", "公主", "女王",
            "达人", "美人", "小姐", "神仙", "小花", "月亮", "宝宝", "月儿", "小白", "小红"
        ]
    name_length                         = random.randint(2, 3) 
    if name_length == 2:
        name                            = random.choice(nicknames_prefix) + random.choice(nicknames_middle)
    else:
        name                            = random.choice(nicknames_prefix) + random.choice(nicknames_middle) + random.choice(nicknames_suffix)
    return name,'xy' if sex=='1' else 'xx',url

async def docx_to_markdown(docx_path=None,fs=None):
    if fs:
        file_stream                     = io.BytesIO(fs.read())
        result                          = mammoth.convert_to_html(file_stream)
        return md(result.value)
    else:
        with open(docx_file, "rb") as docx:
            result                         = mammoth.convert_to_html(docx)
            return md(result.value)

async def pdf_to_markdown(pdf_path=None,fs=None):
    if fs:
        file_stream                     = io.BytesIO(fs.read())
        doc                             = await async_exec(fitz.open,stream=file_stream, filetype="pdf")
    else:
        doc                             = await async_exec(fitz.open,pdf_path)
    html                                = ""
    for page_num in range(doc.page_count):
        page                            = await async_exec(doc.load_page,page_num)
        html                            += page.get_html("html") 
    return md(html)

def html_to_markdown(html_content):
    return md(html_content)



