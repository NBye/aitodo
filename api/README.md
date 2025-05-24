
1. 更新生产
cd /www/projects/aitodo/api
git pull
cd ../dev-api
sudo -u www-data ./run.sh development

cd /www/projects/aitodo/api && git pull && cd ../dev-api

1. 开发环境启动
./run.sh development

2. 生产环境启动
./run.sh production


1. 每个1分钟定时结算AI工资
/crontab/user/auto_salary_settlement

2. 定时生成月佣金账单
/crontab/commission/bill_generate



系统各处模板语法均为Python的jinja2。输出的格式推荐以markdown格式。模板中你的口吻要以  `系统角色` 对智能体说，可以用系统提示作为前缀，加深智能体的控制力。

## **一、角色才智控制引导模板**

参数具体结构可以参考最后的 `附件1`, `附件3`。

### 1. 人设定义模板

- **模板介绍**：此处提示词可以对整个会话进行介绍，包括不限于对各个角色的介绍，以及当前智能体进行角色认知定义。
- **支持参数**：`user` 当前智能体，`users` 聊天室内全部智能体，其中 users 包含 user。
- **缺省模板示例**：
  ```bash
  ## **当前时间**
  {{ 'now' | date }}
  
  ## **当前用户**
  {% for u in users %}
  {% if u._id == user._id %}
  名称: {{ u.nickname }}(你自己)
  {% else %}
  名称: {{ u.nickname }}
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
  ### {{ loop.index }}. {{a.name}}{{':' if a.description else ''}}
  {{a.description}}
  {% endfor %}
  
  {% endif %}
  
  {% endfor %}
  
  Your role is '{{user.nickname}}'. If you need 'help' or 'answers' from 'other users' in the chat room, make sure you mention their name with @, and never @ yourself.
  ```

### 2. 涉及感知模板

- **模板介绍**：多人聊天室中，若用户未@指定智能体回答，则各智能体会通过该提示词进行判断是否需要回答。要求返回Yes|No。
- **支持参数**：`user` 当前智能体, `message` 用户最后的聊天记录, `messages` 聊天记录, messages 不包含 message。
- **缺省模板示例**：
  ```bash
  # 聊天记录:
  {% for m in messages %}
  {{ m.user.nickname }} 说: 
  {{ m.content }}
  
  {% endfor %}
  {{ message.user.nickname }} 说: 
  {{ message.content }}
  
  请根据以上聊天记录判断 用户{{message.user.nickname}} 所说的:“{{message.content}}”，是否与你有关，或向你提问，或向聊天室里的所有人提问。
  是则回复 Yes，不是则回复 No。不要说出你的推理过程。
  ```

### 3. 消息嵌入模板

- **模板介绍**：智能体会根据用户的问题，调用工具并产生相关数据或者引导提示。通过此模板将工具返回嵌入用户问题，引导智能体更专业精准的回复用户。
- **支持参数**：`content` 用户返回提示词，`created` 消息生成时间， `embeddings` 嵌入的工具返回，`user` 可能是user|assistant|system。 即message的所有子属性 。
- **缺省模板示例**：
  ```bash
  {% if embeddings %}
  {% for item in embeddings %}
  ### {{ loop.index }}. 系统调用 {{ item.description }} 返回:
  {{item.output | indent(indent=1,chr='    ')}}
  
  {% endfor %}
  **系统提示: 以上调用是否失败，若有败则优先告知，若无失败则结合返回内容与要求 回复用户的问题（注意请不要说出你的推理过程，不要直接叙述工具返回内容）:**
  {% endif %}
  
  {% if user.role == 'system' %}
  {{content}}
  {% else %}
  <!-- {{user.nickname}}: -->{{content | replace('<think>.*?</think>','') | replace('<!--.*?-->','')}}
  {% endif %}
  ```

### 4. 深度思考模板

- **模板介绍**：智能体对用户所说的问题结合上下文重新理解，进行补全与完善，提高回答的精准。
- **支持参数**：`user` 当前智能体，`message` 用户最后的消息，`messages` 消息记录，其中 messages 不包含 message。
- **缺省模板示例**：
  
  ```bash
  # 聊天记录:
  {% for m in messages %}
  {{ m.user.nickname }} 说: 
  {{ m.content }}
  
  {% endfor %}
  {{ message.user.nickname }} 说: 
  {{ message.content }}
  
  根据聊天记录，理解 {{message.user.nickname}} 最后说的问题:“{{message.content}}”，并站在他的角度，把这个问题不清晰的地方补充完整，重新组织一段更容易理解的文案返回。
  *注意: 直接结返回组织后的文案，不要提及背景信息或你的推理过程。*
  ```

## **二、角色能力控制引导模板**

1. 角色能力没有默认缺省的模板，智能体制造者根据业务自行编写模板。
2. 模板参数具体结构同时支持 `附件1`，`附件2`，`附件3`。

## 附件1

```javascript
message                     = {                                     // 用户的最后一条消息
    "content"               : "hello.",                             // 消息的内容文本
    "role"                  : "assistant",                          // 角色 user|assistant|system
    "user"                  : {
        "_id"               : "a6mXk5QBG63eAWn78PgO",               // 用户ID 
        "nickname"         : "Peter",                               // 用户名称 
        "avatar"           : "/upload/1.png",                       // 头像地址 
        "gender"           : "--",                                  // 性别 --|xx|xy
    }
    "created"               : "2025-02-26 22:30:49",                // 创建时间
    "timestamp"             : 1740580249643,                        // 创建时间戳int,
    "embeddings"            : [
        "description"       : "",                                   // 嵌入内容的描述
        "arguments"         : {},                                   // 嵌入时传入的参数
        "output"            : {},                                   // 嵌入时的输出 可以是对象也可以是字符串
        "type"              : ""                                    // 嵌入的类型，一般是Agent的类型 knowledge|request|generate
    ]
}

messages                    = [message,...],                        // 聊天室内的最大轮次消息，多个message组成，包含system

user                        = {
    "role"                  : "assistant",                          // 角色 user|assistant|system
    "_id"                   : "vuFzk5QBK1CGx1_Eyk0U",               // 用户ID
    "nickname"              : "Lawyer Zhou",                        // 昵称
    "avatar"                : "/static/1.png",                      // 头像地址
    "gender"                : "xx",                                 // 性别
    "birthday"              : "2024-12-01",                         // 生日
    "slogan"                : "I'm your little secretary.",         // 口号
    "join_info"             : {
        "aliasname"         : "",                                   // 组织内昵称
        "remark"            : "",                                   // 组织内备注
        "created"           : "2024-12-01 00:00:00",                // 加入时间
    },
    "action_list"           : [                                     // 用户的技能清单
        {
            "name"          : "",                                   // 技能名称
            "description"   : "",                                   // 技能备注描述
        }
    ]
}
```

## 附件2

```javascript
parameters                  = parameters                            // Ai传入的参数object类型
metadata                                                            // 当前聊天室内的元数据对象（对象内字符不得超过2000字符），
metadata.get(key)           metadata.key                            // 获取元数据值
metadata.set(key)                                                   // 设置元数据值
metadata.delete(key)                                                // 删除一个key
metadata.save({})                                                   // 全量覆盖保存
metadata.update({})                                                 // 增量修改
output                                                              // 当前节点输出数据
parent                      = {                                     // 父级节点
     "output"               : "",                                   // 父级节点输出数据
}
```

## 附件3 （过滤器）

```javascript
merge                        dict | merge(dict)                      // 合并字典，返回合并后的字典
regex                       value | regex(pattern)                  // 判断字符串是否满足正则，返回true|false
indent                      value | indent(indent=1,chr='    ')     // 字符串前边补充字符
replace                     value | replace(pattern,text='')        // 正则替换
date                        'now' | date(format="%Y-%m-%d %H:%M:%S")// 格式化时间 支持int时间戳，字符串时间+1 day，datetime对象。
File                    'file_id' | File                            // 可以获得组织内的文件对象，
    file.download_url(timeout=60)                                   // 获取临时下载地址,超时时间60s
    file.content()                                                  // 获取文件内容
```
