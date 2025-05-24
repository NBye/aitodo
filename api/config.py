import os

MAX_CONTENT_LENGTH                      = os.getenv('MAX_CONTENT_LENGTH')               or 50 * 1024 * 1024  # 50 MB
SEND_FILE_MAX_AGE_DEFAULT               = os.getenv('SEND_FILE_MAX_AGE_DEFAULT')        or 300  # 设置响应最大缓存时间
PERMANENT_SESSION_LIFETIME              = os.getenv('PERMANENT_SESSION_LIFETIME')       or 300  # 设置会话过期时间
QUART_TIMEOUT                           = os.getenv('QUART_TIMEOUT')                    or 300  # 超时时间

# 系统配置
ROOT_DIR                                = os.getenv('AITODO_ROOT_DIR')                  or "/aitodo/api"
MCP_DIR                                 = os.getenv('AITODO_MCP_DIR')                   or "/aitodo/mcp"
UPLOAD_DIR                              = os.getenv('AITODO_UPLOAD_DIR')                or "/aitodo/upload"
STATIC_DIR                              = os.getenv('AITODO_STATIC_DIR')                or "/aitodo/static"
TEMP_DIR                                = os.getenv('AITODO_TEMP_DIR')                  or "/aitodo/temp"
LOG_DIR                                 = os.getenv('AITODO_LOG_DIR')                   or "/aitodo/logs"
PROT                                    = os.getenv('AITODO_PROT')                      or 6100

QUART_ENV                               = os.getenv('QUART_ENV')                        or 'production'

HOST                                    = os.getenv('AITODO_HOST')                      or 'http://localhost:6200'

# /crontab/ 下API 授权IP
ALLOWED_IP                              = os.getenv('ALLOWED_IP')                       or ''

REDIS_OPTIONS                           = {
    'host'                              : os.getenv('REDIS_HOST')                       or '127.0.0.1', 
    'port'                              : os.getenv('REDIS_PORT')                       or 6379, 
    'password'                          : os.getenv('REDIS_PASS')                       or '111111',
    'db'                                : os.getenv('REDIS_DB')                         or 1,
    'max_connections'                   : os.getenv('REDIS_MAX_CONNECTIONS')            or 200,
}


# 系统管理员的 user_id 清单
SYSTEM_ADMIN_USER_IDS                   = os.getenv('SYSTEM_ADMIN_USER_IDS')            or '' 
# 新用户自动分配雇佣的 AI员工 清单
HIRE_ASSISTANT_IDS                      = os.getenv('HIRE_ASSISTANT_IDS')               or ''

# ES 的连接地址
ES_CONNECT_DEFAULT                      = {
    'hosts'                             : (os.getenv('ES_CONNECT_SETTING_HOST')         or 'http://localhost:9200').split(','),
    'basic_auth'                        : tuple((os.getenv('ES_CONNECT_SETTING_AUTH')   or 'elastic,111111').split(',')),
    'verify_certs'                      : False,
    'request_timeout'                   : 180,
}
# 实体索引前缀
ES_INDEX_PREFIX                         = os.getenv('ES_INDEX_PREFIX')                  or 'aitodo_'
# 针对指定索引名配置
# ES_CONNECT_OTHER_INDEX_NAME             = 'xxxxx'

# 系统内置大模型平台
BAILIAN_KEYS                            = os.getenv('BAILIAN_KEYS')                     or ""

# 腾讯云的授权
TENCENT_APPID                           = os.getenv('TENCENT_APPID')                    or ''
TENCENT_SECRETID                        = os.getenv('TENCENT_SECRETID')                 or ''
TENCENT_SECRETKEY                       = os.getenv('TENCENT_SECRETKEY')                or ''

# 腾讯云发送短信，登录使用
TENCENT_SMS_ENDPOINT                    = os.getenv('TENCENT_SMS_ENDPOINT')             or ''
TENCENT_SMS_REGION                      = os.getenv('TENCENT_SMS_REGION')               or ''
TENCENT_SMS_SDKAPPID                    = os.getenv('TENCENT_SMS_SDKAPPID')             or ''
TENCENT_SMS_LOGIN_TEMPLATEID            = os.getenv('TENCENT_SMS_LOGIN_TEMPLATEID')     or ''
TENCENT_SMS_SIGNNAME                    = os.getenv('TENCENT_SMS_SIGNNAME')             or ''

# Email配置，登录使用
EMAIL_SENDER                            = os.getenv('EMAIL_SENDER')                     or ''
EMAIL_AUTH                              = os.getenv('EMAIL_AUTH')                       or ''
EMAIL_SMTP                              = os.getenv('EMAIL_SMTP')                       or ''
EMAIL_PORT                              = os.getenv('EMAIL_PORT')                       or ''
EMAIL_LABEL                             = os.getenv('EMAIL_LABEL')                      or ''

PAY_HOST                                = os.getenv('PAY_HOST')                         or ''
PAY_ACCOUNT_ID                          = os.getenv('PAY_ACCOUNT_ID')                   or ''
PAY_SECRET_KEY                          = os.getenv('PAY_SECRET_KEY')                   or ''
PAY_MERCHANT_ID                         = os.getenv('PAY_MERCHANT_ID')                  or ''

# user,users,
TEMPLATE_DEFINITION                     = os.getenv('TEMPLATE_DEFINITION')              or '''
## **当前时间**
{{ 'now' | date }}

## **当前用户**
{% for u in users %}
{% if u._id == assistant._id %}
名称: {{ u.nickname }}(ID:{{ u._id }} 你自己)
{% else %}
名称: {{ u.nickname }}(ID:{{ u._id }})
{% endif %}
{% if u.gender == 'xy' %}
性别: 男
{% elif u.gender == 'xx' %}
性别: 女
{% endif %}
生日: {{ u.birthday }}
{% if u.action_list %}
技能:
{% for a in u.action_list %}
{{ loop.index }}. {{a.name}}{{':' if a.description else ''}}
{{a.description}}
{% endfor %}

{% endif %}

{% endfor %}

Your role is '{{assistant.nickname}}'. If you need 'help' or 'answers' from 'other users' in the chat room, make sure you mention their name with @, and never @ yourself.
'''.strip()

# user,messages,message
TEMPLATE_RELATED_ME                     = os.getenv('TEMPLATE_RELATED_ME')              or '''
# 聊天记录:
{% for m in messages %}
{% if m.user.nickname %}
{{ m.user.nickname }} 说: 
{% endif %}
{{ m.content }}

{% endfor %}
{{ message.user.nickname }} 说: 
{{ message.content }}

请根据以上聊天记录判断 用户{{message.user.nickname}} 所说的:“{{message.content}}”，是否与你有关，或向你提问，或向聊天室里的所有人提问。
是则回复 Yes，不是则回复 No。请简单概述你的推理过程。
'''

# user,messages,message,reply
TEMPLATE_CHECKREPLY                     = os.getenv('TEMPLATE_CHECKREPLY')              or '''
# 聊天记录:
{% for m in messages %}
{% if m.role=='user' %}
{{ m.user.nickname }} 说: 
{% elif m.role=='assistant' %}
你说:
{% endif %}
{{ m.content }}

{% for item in m.embeddings %}
### {{ loop.index }}. 系统调用 {{ item.description }} 
输入:{{item.arguments}}
输出: {{item.output}}

{% endfor %}

{% endfor %}
{{ message.user.nickname }} 说: 
{{ message.content }}

# 你的最终回答是:
```
{{ reply.content }}
```

结合聊天记录，思考你的回答，是否还需要补充，或者追问？
若是则返回你的: 补充或追问。
不是则返回: Yes
不要返回你的推理过程,返回内容尽量精简。
'''.strip()

TEMPLATE_RECPROMPTS                     = os.getenv('TEMPLATE_RECPROMPTS')              or '''
# 聊天记录:
{% for m in messages %}
{% if m.role=='user' %}
{{ m.user.nickname }} 说: 
{% elif m.role=='assistant' %}
你说:
{% endif %}
{{ m.content }}

{% endfor %}
{{ message.user.nickname }} 说: 
{{ message.content }}

# 你的最终回答是:
```
{{ reply.content }}
```

问题清单：
{{ prompts }}

参考这个清单，思考那些问题更适合接下来的讨论？
你要回复我一个list，其中的元素就是你认为接下来需要讨论的问题,但不能超出问题清单内容。
数量不超过3个，且不能超出，你必须直接返回我list数据，不要返回任何其他，也不要返回你的推理过程。
'''.strip()

# **message
TEMPLATE_EMBEDDINGS                     = os.getenv('TEMPLATE_EMBEDDINGS')              or '''
{% if embeddings %}
## **系统调用工具**

{% for item in embeddings %}
### {{ loop.index }}. 系统调用 {{ item.description }} 
输入: {{item.arguments}}

输出: {{item.output | indent(indent=1,chr='    ')}}

{% endfor %}
你请求的工具调用已完成，请根据调用结果继续回答用户问题。
{% endif %}
'''.strip()



# user,messages,message
TEMPLATE_UNDERSTAND                     = os.getenv('TEMPLATE_UNDERSTAND')              or '''
# 聊天记录:
{% for m in messages %}
{% if m.user.nickname %}
{{ m.user.nickname }} 说: 
{% endif %}
{{ m.content }}

{% endfor %}
{{ message.user.nickname }} 说: 
{{ message.content }}

根据聊天记录，理解 {{message.user.nickname}} 最后说的问题:“{{message.content}}”，并站在他的角度，把这个问题不清晰的地方补充完整，重新组织一段更容易理解的文案返回。
*注意: 直接结返回组织后的文案，不要提及背景信息或你的推理过程。*
''' .strip()