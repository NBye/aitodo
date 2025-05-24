from __future__ import annotations
import os,magic,mimetypes,glob,math,re,json,asyncio
from functools import partial
from PIL import Image,ImageFilter,ImageOps
import aiofiles

from src.super.ESModel import ESModel
from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser

from src.utils.Datetime import Datetime
from src.utils.U62Id import U62Id
from src.utils.errors import CodeError
from src.utils.funcs import log
import base64,shutil,uuid
import config

async def async_open_image(image_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, Image.open, image_path)

async def async_image_save(image,path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, image.save, path)

async def async_makedirs(path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(os.makedirs, path, exist_ok=True))

class EFile(ESModel):

    # 文档类型
    SUPPORT_DOCUMENT_TYPES              = ['pdf','doc','docx','xlsx','ppt','pptx']
    # 文本类型
    SUPPORT_TEXT_TYPES                  = ['py','md','txt']
    # 图片类型
    SUPPORT_IMG_TYPES                   = ['jpg','png','gif','jpeg']
    # 音频类型
    SUPPORT_AUDIO_TYPES                 = ['mp3','wav']
    # 视频类型
    SUPPORT_VIDEO_TYPES                 = ['m4a','mp4','avi','mkv']
    # 二进制类型
    SUPPORT_BINARY_TYPES                = [
                                        *SUPPORT_DOCUMENT_TYPES,
                                        *SUPPORT_AUDIO_TYPES,
                                        *SUPPORT_VIDEO_TYPES,
    ]
    URL_PREFIX                          = '/upload/'

    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        'location'                      : 'public',
        'remark'                        : '',
        'name'                          : '',
    }
    MAPPING                             = {
        "settings"                      : {
            "index"                     : {
                "refresh_interval"      : "1s",
            }
        },
        "mappings"                      : {
            "dynamic"                   : "false", 
            "properties"                : {
                "user_id"               : {"type": "keyword"}, 
                "organization_id"       : {"type": "keyword"}, 
                "type"                  : {"type": "keyword"}, # jpg|png|text|...
                "location"              : {"type": "keyword"}, # public|private
                # "permission"            : {"type": "keyword"}, # private|

                "name"                  : {"type": "text"},
                "remark"                : {"type": "text"},
                "url"                   : {"type": "keyword","index":False}, 
                "size"                  : {"type": "integer"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
            }
        }
    }

    @classmethod
    def _support_groups(cls):
        return [
            {'icon':'icon-image',   'type':'image',     'count':0,'size':0, 'name':'图片',  'supported':'png,jpg,jpeg,gif'},
            {'icon':'icon-docs',    'type':'document',  'count':0,'size':0, 'name':'文档',  'supported':'pdf,doc,docx,txt,xlsx,md,ppt,pptx'},
            {'icon':'icon-audio',   'type':'audio',     'count':0,'size':0, 'name':'音频',  'supported':'mp3,wav,m4a'},
            {'icon':'icon-video',   'type':'video',     'count':0,'size':0, 'name':'视频',  'supported':'mp4,avi,mkv'},
            {'icon':'icon-folder',  'type':'other',     'count':0,'size':0, 'name':'其他',  'supported':'other'},
        ]

    @classmethod
    async def upload_binary(cls,binary,name,user:EUser,organization:EOrganization=None,location='public',refresh=True,remark=''):
        u62id                           = U62Id.generate(12)
        fname                           = "/".join([u62id[i:i+2] for i in range(0, len(u62id), 2)])
        file_path                       = f'{config.UPLOAD_DIR}/{location}/{os.path.dirname(fname)}'
        file_name                       = os.path.basename(fname)
        await async_makedirs(file_path)
        ext                             = os.path.splitext(name)[1][1:]
        sycname                         = f"{file_path}/{file_name}.{ext}"
        async with aiofiles.open(sycname, 'wb') as f:
            await f.write(binary)
        try:
            return await super().create(
                refresh                 = refresh,
                user_id                 = user._id,
                organization_id         = organization._id if organization else None,
                type                    = ext,
                name                    = name,
                url                     = f'{cls.URL_PREFIX}{location}/{fname}.{ext}',
                size                    = len(binary),
                location                = location,
                remark                  = remark,
            )
        except BaseException as e:
            if os.path.exists(sycname):
                await aiofiles.remove(sycname)
            raise e

    @classmethod
    async def upload(cls,rfile,user:EUser,organization:EOrganization=None,location='public',refresh=True,remark=''):
        ext                             = os.path.splitext(rfile.filename)[1][1:]
        if ext=='' or (ext not in cls.SUPPORT_IMG_TYPES and ext not in cls.SUPPORT_BINARY_TYPES and ext not in cls.SUPPORT_TEXT_TYPES):
            raise CodeError(f'不支持 .{ext} 的文件类型')
        if organization and user._id and not await EOrganizationUser.afrom(organization_id=organization._id,user_id=user._id):
            raise CodeError(f'无权限上传',403)
        if organization:
            # print(json.dumps(organization,indent=4, ensure_ascii=False))
            aggs                        = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
                {"term": {"organization_id": organization._id}},
            ]}})
            if (aggs['total_size']['value'])/(1024**3) >= organization.settings['storage_limit']:
                raise CodeError(f'当前组织存储不足,请删除一些文件。')
        else:
            aggs                        = await EFile.aggs({"total_size": {"sum": {"field": "size"}}},query={"bool": {"must": [
                {"term": {"organization_id": ""}},
                {"term": {"user_id": user._id}}
            ]}})
            if (aggs['total_size']['value'])/(1024**3) >= user.settings['storage_limit']:
                raise CodeError(f'您的个人存储不足,请删除一些文件。')
        u62id                           = U62Id.generate(12)
        fname                           = "/".join([u62id[i:i+2] for i in range(0, len(u62id), 2)])
        file_path                       = f'{config.UPLOAD_DIR}/{location}/{os.path.dirname(fname)}'
        file_name                       = os.path.basename(fname)
        await async_makedirs(file_path)
        tmpname                         = f"{file_path}/{file_name}.tmp"
        sycname                         = f"{file_path}/{file_name}.{ext}"
        async with aiofiles.open(tmpname, 'wb') as f:
            mime                        = False
            size                        = 0
            while True:
                chunk                   = rfile.stream.read(1024) #1kb
                size                    += len(chunk)
                if not chunk:
                    break
                if mime == False:
                    mime                = magic.Magic(mime=True)
                    mime_type           = mime.from_buffer(chunk) or []
                    mime_exts           = mimetypes.guess_extension(mime_type) or []
                    # print(rfile.filename,mime_type,mime_exts,ext)
                    if ext in mime_type or ext in mime_exts:
                        pass # 真实且支持的类型
                    elif 'image' in mime_type:
                        pass # 图片拓展名不正确也可接受
                    elif ext in cls.SUPPORT_TEXT_TYPES and mime_exts=='.txt':
                        pass # 可接受的代码文本类型
                    elif ext in ['doc','docx','xlsx'] and mime_type in ['application/zip','application/CDFV2']:
                        pass # word 格式特殊mime
                    else:
                        await aiofiles.remove(tmpname)
                        raise CodeError(f'The "{mime_type}" cannot use the "{ext}".')
                await f.write(chunk)
            try:
                os.rename(tmpname, sycname)
                efile                   = await cls.create(
                        refresh         = refresh,
                        user_id         = user._id,
                        organization_id = organization._id if organization else None,
                        type            = ext,
                        name            = rfile.filename,
                        url             = f'{cls.URL_PREFIX}{location}/{fname}.{ext}',
                        size            = size,
                        location        = location,
                        remark          = remark,
                )
                return efile
            except BaseException as e:
                if os.path.exists(tmpname):
                    await aiofiles.remove(tmpname)
                if os.path.exists(sycname):
                    await aiofiles.remove(sycname)
                raise e

    @classmethod
    async def visibility(cls,url,token=None,tmp_token=None):
        if tmp_token:
            from src.entity.ECache import ECache
            if data := await ECache.getData(tmp_token):
                return EFile(**data)
            else:
                return None
        elif token:
            try:
                token,user,session      = await EUser.login(type='0',token=token)
            except:
                return None
        else:
            return None
        efile                           = await cls.afrom(url=url)
        if efile==None:
            return None
        organization_id                 = session.get('organization_id',None)
        if organization_id and efile.organization_id:
            return efile
        if efile.user_id == user._id:
            return efile
        return None
 
    @classmethod
    def isImage(cls,url):
        ext                             = os.path.splitext(url)[1][1:]
        return ext in cls.SUPPORT_IMG_TYPES

    @classmethod
    async def mergeImage(cls,urls:list,user:EUser,organization:EOrganization=None,location='public',refresh=True,remark=''):
        images                          = []
        for path in urls[:9]:
            if re.match(r'^/upload/.+\.(jpg|png|gif|jpeg)$', path):
                images.append(await async_open_image(f'{config.UPLOAD_DIR}/{path[8:]}'))
            elif re.match(r'^/static/.+\.(jpg|png|gif|jpeg)$', path):
                images.append(await async_open_image(f'{config.STATIC_DIR}/{path[8:]}'))
        n                               = len(images)
        if n==0:
            return 'No merge image found !',404
        elif n==1:
            positions                   = [[(120,120),(0,0)]]  #[(w.h),(x,y)]
        elif n==2:
            positions                   = [[(60,120),(0,0)],[(60,120),(60,0)]]
        elif n==3:
            positions                   = [[(40,120),(0,0)],[(40,120),(40,0)],[(40,120),(80,0)]]
        elif n==4:
            positions                   = [[(60,60),(0,0)],[(60,60),(60,0)],
                                            [(60,60),(0,60)],[(60,60),(60,60)]]
        elif n==5:
            positions                   = [
                                            [(40,40),(0,20)],  [(40,40),(40,20)], [(40,40),(80,20)],
                                            [(40,40),(0,60)], [(40,40),(40,60)]
                                        ]
        elif n==6:
            positions                   = [
                                            [(40,40),(0,20)],  [(40,40),(40,20)], [(40,40),(80,20)],
                                            [(40,40),(0,60)], [(40,40),(40,60)],[(40,40),(80,60)]
                                        ]                                
        elif n==7:
            positions                   = [
                                            [(40,40),(0,0)],  [(40,40),(40,0)], [(40,40),(80,0)],
                                            [(40,40),(0,40)], [(40,40),(40,40)],[(40,40),(80,40)],
                                            [(40,40),(0,80)]
                                        ]
        elif n==8:
            positions                   = [
                                            [(40,40),(0,0)],  [(40,40),(40,0)], [(40,40),(80,0)],
                                            [(40,40),(0,40)], [(40,40),(40,40)],[(40,40),(80,40)],
                                            [(40,40),(0,80)], [(40,40),(40,80)]
                                        ]
        elif n>=9:
            positions                   = [
                                            [(40,40),(0,0)],  [(40,40),(40,0)], [(40,40),(80,0)],
                                            [(40,40),(0,40)], [(40,40),(40,40)],[(40,40),(80,40)],
                                            [(40,40),(0,80)], [(40,40),(40,80)],[(40,40),(80,80)]
                                        ]
        composite_image                 = Image.new('RGB', (120, 120), color='white')
        for i,position in enumerate(positions):
            w,h                         = position[0]
            x,y                         = position[1]
            img                         = images[i]
            # 重置图片大小
            o_w, o_h                    = img.size
            # 计算缩放比例
            w_ratio                     = w / o_w
            h_ratio                     = h / o_h
            scale_ratio                 = max(w_ratio, h_ratio)
            n_w                         = int(o_w * scale_ratio)
            n_h                         = int(o_h * scale_ratio)
            # 缩放图片
            resized_image               = img.resize((n_w, n_h), Image.LANCZOS)
            new_image                   = Image.new(img.mode, (w, h), (255, 255, 255, 1))
            # 计算居中位置
            px                          = (w - n_w) // 2
            py                          = (h - n_h) // 2
            # 将缩放后的图片粘贴到背景上
            new_image.paste(resized_image, (px, py))
            images[i]                   = new_image
            composite_image.paste(new_image, box=(x, y))
        ext                             = 'png'
        u62id                           = U62Id.generate(12)
        fname                           = "/".join([u62id[i:i+2] for i in range(0, len(u62id), 2)])
        file_path                       = f'{config.UPLOAD_DIR}/{location}/{os.path.dirname(fname)}'
        await async_makedirs(file_path)
        await async_image_save(composite_image,f'{config.UPLOAD_DIR}/{location}/{fname}.{ext}')
        efile                           = await cls.create(
                refresh                 = refresh,
                user_id                 = user._id,
                organization_id         = organization._id if organization else None,
                type                    = ext,
                name                    = f'{u62id}.{ext}',
                url                     = f'{cls.URL_PREFIX}{location}/{fname}.{ext}',
                size                    = len(composite_image.tobytes()),
                location                = location,
                remark                  = remark,
        )
        return efile

    async def http_url(self):
        return f'{config.HOST}{self.url}'
   
    async def temp_url(self,seconds=60*30):
        from src.entity.ECache import ECache
        token                           = str(uuid.uuid4())
        await ECache.setData(token, seconds,refresh=True,
            **self
        )
        return f'{await self.http_url()}?token={token}'

    def is_image(self):
        return self.type in self.SUPPORT_IMG_TYPES

    def is_audio(self):
        return self.type in self.SUPPORT_AUDIO_TYPES

    def is_video(self):
        ext                             = os.path.splitext(self.url)[1][1:]
        return self.type in self.SUPPORT_VIDEO_TYPES

    async def to_safe_dict(self):
        return {
            'type'                      : self.type,
            'location'                  : self.location,
            'name'                      : self.name,
            'url'                       : await self.http_url(),
        }

    async def to_string(self):
        string                          =  f'文件ID: {self._id}\n'
        string                          += f'文件名: {self.name}\n'
        string                          += f'文件大小: {self.size}bit\n'
        string                          += f'文件格式: .{self.type}\n'
        string                          += f'文件网址: {await self.http_url()}\n'
        return string


    async def resize(self, w=0, h=0, m=0):
        prefix_len                      = len(self.__class__.URL_PREFIX)
        path                            = f'{config.UPLOAD_DIR}/{os.path.dirname(self.url)[prefix_len:]}'
        cpath                           = f'{config.TEMP_DIR}/{os.path.dirname(self.url)[prefix_len:]}'
        ext                             = os.path.splitext(self.url)[1]
        name                            = os.path.basename(self.url)[0:-len(ext)]
        src_path                        = f'{path}/{name}{ext}'
        cut_path                        = f'{path}/{name}{ext}'
        if w==0 and h==0:
            return os.path.dirname(self.url[prefix_len+len(self.location)+1:])+f'/{name}{ext}'
        image                           = await async_open_image(src_path)
        o_w, o_h                        = image.size
        # 计算缩放比例
        w_ratio                         = w / o_w
        h_ratio                         = h / o_h
        if h == 0 and w>0:
            scale_ratio                 = w_ratio
            h                           = int(w_ratio * o_h)
        elif w == 0 and h>0:
            scale_ratio                 = h_ratio
            w                           = int(h_ratio * o_w)
        elif m == 0:  # 长边100%
            scale_ratio                 = min(w_ratio, h_ratio)
        elif m == 1:  # 短边100%
            scale_ratio                 = max(w_ratio, h_ratio)
        else:
            raise CodeError('不支持的缩放模式')
        tmp_path                        = f'{cpath}/{name}-{w}-{h}-{m}{ext}'
        if not os.path.exists(cpath):
            await async_makedirs(cpath)
        if not os.path.exists(tmp_path):
            # 计算新尺寸
            n_w                         = int(o_w * scale_ratio)
            n_h                         = int(o_h * scale_ratio)
            # 缩放图片
            resized_image               = image.resize((n_w, n_h), Image.LANCZOS)
            background                  = Image.new(image.mode, (w, h), (255, 255, 255, 0))
            # 计算居中位置
            x                           = (w - n_w) // 2
            y                           = (h - n_h) // 2
            # 将缩放后的图片粘贴到背景上
            background.paste(resized_image, (x, y))
            await async_image_save(background,tmp_path)
        return os.path.dirname(self.url[prefix_len+len(self.location)+1:])+f'/{name}-{w}-{h}-{m}{ext}'
    
    def get_path(self):
        prefix_len                      = len(self.__class__.URL_PREFIX)
        path                            = f'{config.UPLOAD_DIR}/{os.path.dirname(self.url)[prefix_len:]}'
        ext                             = os.path.splitext(self.url)[1]
        name                            = os.path.basename(self.url)[0:-len(ext)]
        file_path                       = f'{path}/{name}{ext}'
        return file_path

    async def base64_data(self):
        file_path                       = self.get_path()
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                file_data                   = await file.read()
                base64_data                 = base64.b64encode(file_data).decode('utf-8')
                mime_type, _                = mimetypes.guess_type(file_path)
                if mime_type is None:
                    mime_type               = 'application/octet-stream'
                return f"data:{mime_type};base64",base64_data
        except BaseException as e:
            pass
        return None,None
    
    async def move_to(self,efile):
        directory                       = os.path.dirname(efile.get_path())
        if not os.path.exists(directory):
            await async_makedirs(directory)
        shutil.move(self.get_path(), efile.get_path())
        ext                             = os.path.splitext(efile.url)[1]
        name                            = os.path.basename(efile.url)[0:-len(ext)]
        file_pattern                    = os.path.join(directory, f'{name}-*')
        files_to_delete                 = glob.glob(file_pattern)
        for file_path in files_to_delete:
            try:
                await aiofiles.remove(file_path)
            except Exception as e:
                await log(f'Error deleting {file_path}: {e}')
        await efile.upset(size=self.size,type=self.type)
        await self.destroy()

    async def destroy(self,refresh=True):
        prefix_len                      = len(self.__class__.URL_PREFIX)
        directory                       = f'{config.UPLOAD_DIR}/{os.path.dirname(self.url)[prefix_len:]}'
        ext                             = os.path.splitext(self.url)[1]
        name                            = os.path.basename(self.url)[0:-len(ext)]
        file_pattern                    = os.path.join(directory, f'{name}*')
        files_to_delete                 = glob.glob(file_pattern)
        for file_path in files_to_delete:
            try:
                await aiofiles.remove(file_path)
            except Exception as e:
                await log(f'Error deleting {file_path}: {e}')
        return await super().destroy(refresh=refresh)