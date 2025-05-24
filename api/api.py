from quart import Quart, send_from_directory,jsonify,request
from urllib.parse import urlparse

from src.entity.EFile import EFile
from src.utils.errors import CodeError 

from src.super.controllers import getToken

import traceback,os
import config

from src.utils.model.models import  import_module  # 预加载一些模块

app                                     = Quart(__name__,static_folder=config.STATIC_DIR)
app.config.update(
    MAX_CONTENT_LENGTH                  = config.MAX_CONTENT_LENGTH,
    SEND_FILE_MAX_AGE_DEFAULT           = config.SEND_FILE_MAX_AGE_DEFAULT,
    PERMANENT_SESSION_LIFETIME          = config.PERMANENT_SESSION_LIFETIME,
    QUART_TIMEOUT                       = config.QUART_TIMEOUT,
)
@app.after_request
async def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
    response.headers.add('Access-Control-Allow-Headers', 'content-type,x-requested-with,token,store-hash,my-encryption,request-id,client-id,clientid,api-version,set-cookie,cookie')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '1728000')
    token                               = getattr(response, 'token',None)
    if token and token != request.cookies.get('token'):
        domain                          = ".".join(request.host.split(".")[-2:])
        response.headers.add('Set-Cookie', f'token={token}; Domain={domain}; Max-Age=2592000; Path=/')
    return response

@app.route('/upload/<location>/<path:filename>')
async def upload_static(location,filename):
    url                                 = f'/upload/{location}/{filename}'
    efile                               = None
    if location == 'private':
        efile                           = await EFile.visibility(url,token=getToken(),tmp_token=request.args.get('token'))
        if efile == None:
            return 'No Permission to Access !',401
    elif location == 'storage':
        efile                           = await EFile.visibility(url,token=getToken(),tmp_token=request.args.get('token'))
        if efile == None:
            return 'No Permission to Access !',401
    if EFile.isImage(url):
        if efile == None:
            efile                       = await EFile.afrom(url=url)
        if efile == None:
            return await send_from_directory(config.STATIC_DIR, '404.svg')
        w                               = int(request.args.get('w', default=0)) # 最大宽度
        h                               = int(request.args.get('h', default=0)) # 最大高度
        m                               = int(request.args.get('m', default=0)) # 模式 0长边100%短边镂空，1短边100%场边裁剪 中心居中。
        if (w>0 or h>0) and efile.type !='gif':
            filename                        = await efile.resize(w=w,h=h,m=m)
            file_path                   = config.TEMP_DIR+ '/'+ f'{location}/{filename}'
        else:
            file_path                   = config.UPLOAD_DIR+ '/'+ f'{location}/{filename}'
    else:
        file_path                       = config.UPLOAD_DIR+ '/'+ f'{location}/{filename}'
    directory, filename                 = os.path.split(file_path)
    response                            = await send_from_directory(directory, filename)
    if efile and not EFile.isImage(url):
        response.headers['Content-Disposition'] = f'attachment; filename="{efile.name}"'
    return response

@app.route('/<group>/<controller>/<path:action>', methods=['POST','GET','OPTIONS'])
async def serve_api(group,controller,action):
    params                              = action.split('/')
    action                              = params.pop(0)
    try:  
        module                          = import_module(f"src.controller.{group}.{controller.capitalize()}")
        c                               = getattr(module, controller.capitalize())()
        await c._async_init()
        a                               = getattr(c,action)
        pargs                           = []
        pdict                           = {}
        for p in params:
            ps                          = p.split(':')
            if len(ps) > 1:
                pdict[ps[0]]            = ps[1]
            else:
                pargs.append(ps[0])
        ret                             = await a(*pargs,**pdict)
        if isinstance(ret,tuple):
            response                    = jsonify({
                "code"                  : ret[2] if len(ret)>2 else 1,
                "message"               : ret[1] if len(ret)>1 else '',
                "data"                  : ret[0] if len(ret)>0 else {},
            })
        elif isinstance(ret,dict):
            response                    = jsonify(ret)
        else:
            response                    = ret
        response.token                  = getattr(c,'token',None)
        response.headers['Connection'] = 'keep-alive'
        return response
    except BaseException as e:  
        code                            = getattr(e,'code') if hasattr(e,'code') else 500
        data                            = getattr(e,'data') if hasattr(e,'data') else {}
        if isinstance(e, CodeError):
            return jsonify({
                "code"                  : code,
                "message"               : str(e),
                "data"                  : data,
            })  
        else:
            return jsonify({
                "code"                  : code,
                "message"               : str(e),
                "data"                  : data,
                "trace"                 : traceback.format_exc()  
            })
    
@app.route('/')
@app.route('/<path:action>')
async def serve_default(action='',):
    return f'/{str(action)} ok !'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PROT, debug=True,use_reloader=True)


