# 网音·AiTodo

网音·AiTodo是一个 智能体与人类共同工作的即时通讯WEB服务程序。这里支持A2A、MCP、知识库、工作流、思维连、crontab任务、自定义Tools、Request Tools，总之你想要的都在这里。

网音·AiTodo 简化了私有化下智能体的部署，解决了大规模智能体的管理困难，降低了智能体的学习与使用门槛，连接了人类与AI和平共处的工作方式。

此程序可以配置短信登录，邮箱登录。系统内有测试数据，可用一下账号进行体验。

    测试账号：tester@netsound.co
    测试密码：111111

本系统通过Dockerfile部署，内置Elasticsearch、Redis、Anaconda3、NodeJS、Code-Server、Supervisor、nginx 构建镜像可能时间会较长，并且需要科学上网。

本项目预览地址：[https://ai2do.co](https://ai2do.co)

### 目录

1. 代码结构
2. 安装部署
   - 2.1 构建镜像
   - 2.2 修改环境变量
   - 2.3 启动容器
   - 2.4 检查服务
3. 开始使用
   - 无法登录？
   - 配置密钥
   - 绑定大模型
   - 欢迎使用
4. 其他
   - MCP
   - A2A
   - Request Tools
   - workflow
   - open api
   - knowledge base
   - file manager
   - task

### 1. 代码结构

- aitodo/
  - api *接口服务python服务程序*
    - src/ *源码目录*
    - test/ *测试代码目录*
    - api.py *AIP启动入口程序*
    - consumer.py *Task消费服务入程序*
    - config.py *环境变量默认值配置程序*
    - run.sh *手动启动服务入口程序（测试时可能使用）*
    - environment.yml *初始化conda python 环境配置（docker 自动使用）*
  - client/ *系统vue+vite前端程序*
    - public/ *前端公共静态文件存放目录*
    - src/ *前端源码目录*
  - mcp/ *MCP安装目录*
    - {mcp-key-name}/ *MCP的 key name。*
      - config.json *MCP的json配置*
  - data/ *docker容器挂在的一些目录*
    - code-server/ *code-server 相关配置，如：密码*
    - es/ *Elasticsearch 数据挂载目录*
    - elasticsearch.yml *Elasticsearch 配置挂载文件*
    - nginx/ *Nginx /etc/nginx/conf.d 的挂在位置*
    - redis/ *Redis数据目录位置*
    - supervisor/ *supervisor /etc/supervisor/conf.d 的挂在目录*
  - static/ *静态文件目录*
  - upload/ *系统上传文件图片存放目录*
  - logs/ *系统日志存放目录*
  - temp/ *系统缓存存放目录（可随意清空）*
  - Dockerfile *生成docker环境*

### 2. 安装部署

#### 2.1 构建镜像

```shell
# 进入项目目录
cd  aitodo 
# 构建docker镜像，此环节时间较长，并且注意科学上网。
docker build --no-cache -t aitodo-docker .
```

#### 2.2 修改环境变量

```shell
vim data/supervisor/aitodo.conf
# 修改 environment 项目的值

# ES数据库必填
# ES_CONNECT_SETTING_HOST="http://localhost:9200，ES数据库链接地址，docker默认创建的就是这个。"

# EMAIL相关可以开启邮箱注册登录
# EMAIL_SENDER="email@netsound.com 发送者的邮箱"
# EMAIL_AUTH="SMTP密码"
# EMAIL_SMTP="smtp.qq.com SMTP host"
# EMAIL_PORT="587 SMTP 对应端口",
# EMAIL_LABEL="网音·AiTodo 发送者邮箱显示的名称"

# 腾讯云的授权可以开启手机验证码注册登录
# TENCENT_APPID=
# TENCENT_SECRETID =
# TENCENT_SECRETKEY  =
# TENCENT_SMS_ENDPOINT=
# TENCENT_SMS_REGION=
# TENCENT_SMS_SDKAPPID=
# TENCENT_SMS_LOGIN_TEMPLATEID=
# TENCENT_SMS_SIGNNAME= 
```
当然，您可以开修改 api/config.py 中的默认值，这样就不需要环境变量配置了。

#### 2.3 启动容器

linux bash shell 下 执行
```shell
docker run -d \
   -p 6379:6379 \
   -p 9200:9200 \
   -p 9001:9001 \
   -p 6100:6100 \
   -p 6200:6200 \
   -p 8080:8080 \
   -v ${pwd}/api:/aitodo/api \
   -v ${pwd}/mcp:/aitodo/mcp \
   -v ${pwd}/client:/aitodo/client \
   -v ${pwd}/static:/aitodo/static \
   -v ${pwd}/upload:/aitodo/upload \
   -v ${pwd}/temp:/aitodo/temp \
   -v ${pwd}/logs:/aitodo/logs \
   -v ${pwd}/data/redis:/var/lib/redis \
   -v ${pwd}/data/es:/var/lib/elasticsearch \
   -v ${pwd}/data/code-server:/root/.config/code-server \
   -v ${pwd}/data/supervisor:/etc/supervisor/conf.d \
   -v ${pwd}/data/nginx:/etc/nginx/conf.d \
   -v ${pwd}/data/elasticsearch.yml:/etc/elasticsearch/elasticsearch.yml \
   --name aitodo aitodo-docker
```
windows PowerShell 下执行
```shell
docker run -d `
   -p 6379:6379 `
   -p 9200:9200 `
   -p 9001:9001 `
   -p 6100:6100 `
   -p 6200:6200 `
   -p 8080:8080 `
   -v ${PWD}/api:/aitodo/api `
   -v ${PWD}/mcp:/aitodo/mcp `
   -v ${PWD}/client:/aitodo/client `
   -v ${PWD}/static:/aitodo/static `
   -v ${PWD}/upload:/aitodo/upload `
   -v ${PWD}/temp:/aitodo/temp `
   -v ${PWD}/logs:/aitodo/logs `
   -v ${PWD}/data/redis:/var/lib/redis `
   -v ${PWD}/data/es:/var/lib/elasticsearch `
   -v ${PWD}/data/code-server:/root/.config/code-server `
   -v ${PWD}/data/supervisor:/etc/supervisor/conf.d `
   -v ${PWD}/data/nginx:/etc/nginx/conf.d `
   -v ${PWD}/data/elasticsearch.yml:/etc/elasticsearch/elasticsearch.yml `
   --name aitodo aitodo-docker
```
   
### 3.4 检查服务

3.4.1 检查 supervisor 是否正常

    浏览器打开: http://localhost:9001/，是否显示
<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/supervisor.png">

3.4.2 检查 Elasticsearch 是否正常
    
    浏览器打开：http://localhost:9200/ 是否正常显示。
    ES 启动相对较慢，如果supervisor显示ES已启动，可以等3分钟。
<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/es.png">
    

3.4.3 检查 API 是否正常
    
    浏览器打开：http://localhost:6100/ 是否显示 ok !

3.4.4 检查客户端是否正常

    浏览器打开：http://localhost:6200/ 是否显示正常
<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/index.png">


### 3. 开始使用

#### 3.1 无法登录？

3.1.1 请检查环境变量是否没有配置: data/supervisor/aitodo.conf ,若修改环境变量后需重载docker中的supervisor。
```shell
docker exec aitodo bash -c "supervisorctl reread && supervisorctl update"
```

3.1.2 使用测试账号

    测试账号：tester@netsound.co
    测试密码：111111

#### 3.2 配置密钥

3.2.1 头像>组织设置>Nvidia 点击启用后，输入密钥，再点击更新模型。

3.2.2 出现模型列表后，选择喜欢的模型，并标记模型能力。别忘了点击保存。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/aipkey.png">

#### 3.3 绑定大模型

3.3.1 成员>点击详情>参数信息 点击选择就可以设置模型。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/bind.png">

3.3.2 当然点击成员详情中的编辑，有全的设置。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/bind2.png">


#### 3.4 欢迎使用

最后欢迎您的使用。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/hello.png">



### 4. 其他

#### 4.1 MCP

可以接入任何外部的MCP，如果自己业务需求可以针对开发MCP拷贝到 /aitodo/mcp/ 文件夹下，按规划配置。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/mcp.png">

#### 4.2 A2A

系统中支持多人多AI即使通信，AI之间会自动跟对方的能力@对方衔接工作，当然这个能力也是可以在Ai的模板设置中定制的。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/a2a.png">

#### 4.3 Request Tools

MCP固然好用，但是原业务中已有很多API了，在不开发的情况下，使用这些API可能要比MCP来的快。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/request.png">

#### 4.4 workflow

工作六种，可以串入MCP、Request Tools、知识库 等。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/workflow.png">

#### 4.5 open api

外部系统可以使用本项目中的API，也可以向大模型一样使用。只不过是多了内置Tools显得更加智能与准确。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/sercrt.png">
   
#### 4.6 knowledge base

知识库并不可少，使用简单。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/knowlage.png">

#### 4.7 file manager

文件管理，可以在对话过程中使用让AI理解和修改。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/file.png">

#### 4.8 Task

Task 更是重要，可以延迟任务，周期任务，Crontab 的方式编排。结合工作流，AI可以自主的互相安排工作，并在适当的时候执行。

<img style="height:200px" src="https://netsound.oss-cn-beijing.aliyuncs.com/aitodo/poster/task.png">

