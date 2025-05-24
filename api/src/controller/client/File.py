import traceback
from quart import request
from src.super.controllers import OrganizationController

from src.entity.EUser import EUser
from src.entity.EOrganization import EOrganization
from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EFile import EFile

from src.utils.errors import CodeError
from src.utils.funcs import byteFormat

import config

class File(OrganizationController):
   
    async def checkOrganizationPermission(self,organization_id,is_raise=True):
        ou                              = await EOrganizationUser.afrom(organization_id=organization_id,user_id=self.user._id)
        if not ou:
            if is_raise:
                raise CodeError('无权限查看',403)
            else:
                return False
        return True

    async def upload(self):
        post                            = await self.get_post()
        data                            = {}
        private                         = str(post.get('private'))=='1'
        refresh                         = 'true' if post.get('refresh') else 'false'
        organization_id                 = post.get('organization_id')
        if organization_id:
            organization                = await EOrganization.afrom(_id=organization_id,_must=True)
        else:
            organization                = None
        
        files                           = await request.files
        for k,fs in files.items():
            try:
                if private:
                    efile               = await EFile.upload(fs, self.user, organization=organization, location='private',refresh=refresh)
                else:
                    efile               = await EFile.upload(fs, self.user, organization=organization, location='public',refresh=refresh)
                data[k]                 = {**efile,**{'status':'success','reason': ''}}
            except BaseException as e:
                data[k]                 = {'status':'failed','reason': str(e),'stack':traceback.format_exc()} 
        return data,

    async def upset(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        file_id                         = post.get('file_id','')
        verify                          = [
            ('name',        [1,50],     None,   '名称需要1~50个字符'),
            ('remark',      [0,100],     None,   '备注需要100个字符以内'),
        ]
        data                            = await self._check_data(None,verify)
        efile                           = await EFile.afrom(_id=file_id)
        if not efile:
            raise CodeError('文件不存在')
        if organization_id:
            await self.checkOrganizationPermission(organization_id)
        elif efile.user_id != self.user._id:
            raise CodeError('无权限修改',403)
        await efile.upset(**data)
        return {'file':efile},'修改成功'

    async def info(self):
        post                            = await self.get_post()
        file_id                         = post.get('file_id','')
        efile                           = await EFile.afrom(_id=file_id)
        if not efile:
            raise CodeError('文件不存在')
        elif efile.organization_id:
            if not await EOrganizationUser.afrom(organization_id=efile.organization_id, user_id=self.user._id):
                raise CodeError('无权限查看1',403)
        elif efile.user_id != self.user._id:
            raise CodeError('无权限查看2',403)
        user                            = await self.getUser(efile.user_id)
        if efile.organization_id:
            organization                = await self.getOrganization(efile.organization_id)
            if user:
                user['join_info']       = await organization.getJoinInfo(user)
                if user['join_info']==None:
                    raise CodeError('无权限查看3',403)
        else:
            organization                = None
        return {'file':efile,'user':user.desensitization('avatar,nickname,join_info') if user else None,'organization':organization.desensitization('name,avatar') if organization else None},

    async def statistics(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        organization                    = None
        query                           = {"bool": {"filter": []}}
        if organization_id:
            await self.checkOrganizationPermission(organization_id)
            query['bool']['filter'].append({"term": {"organization_id": organization_id}})
            organization                = await self.getOrganization(organization_id)
        else:
            query['bool']['filter'].append({"term": {"user_id": self.user._id}})
            query['bool']['filter'].append({"term": {"organization_id": ''}})
        aggs                            = await EFile.aggs({
            "group_by_type"             : {
                "terms"                 : {
                    "field"             : "type",
                    "size"              : 50
                },
                "aggs"                  : {
                    "total_size"        : {
                        "sum"           : {
                            "field"     : "size"
                        }
                    }
                }
            }
        },query=query)
        groups                          = EFile._support_groups()
        size                            = 0
        count                           = 0
        for item in aggs['group_by_type']['buckets']:
            ext                         = item['key']
            num                         = item['doc_count']
            tot                         = item['total_size']['value']
            ind                         = False
            count                       += num
            size                        += tot
            for group in groups:
                if ext in group['supported']:
                    group['count']      += num
                    group['size']       += tot
                    ind                 = True
                    break
            if ind == False:
                groups[4]['count']      +=num
                groups[4]['size']       +=tot
        for group in groups:
            group['description']        = f'文件数: {group["count"]}, 存储: {byteFormat(group["size"])}'
        if organization:
            limit                       = organization['settings']['storage_limit']
        else:
            limit                       = self.user['settings']['storage_limit']
        return {'list':groups,'storage':{'limit':limit*1024*1024*1024,'size':size,'count':count}},

    async def search(self):
        post                            = await self.get_post()
        organization_id                 = post.get('organization_id','')
        keyword                         = post.get('keyword','')
        supported                       = post.get('supported','')
        skip                            = int(post.get('skip',0))
        size                            = int(post.get('size',10))
        sort_list                       = await self.splitSortList()
        query                           = {
            "bool"                      : {"must":[]},
        }
        if organization_id:
            await self.checkOrganizationPermission(organization_id)
            query['bool']['must'].append({"term": {"organization_id": organization_id}})
        else:
            query['bool']['must'].append({"term": {"user_id": self.user._id}})
            query['bool']['must'].append({"term": {"organization_id": ""}})

        if supported=='other':
            types                       = []
            for group in EFile._support_groups():
                if group['supported']!='other':
                    types               += group['supported'].split(',')
            query['bool']['must_not']   = [{"terms": {"type": types}}]
        elif supported:
            query['bool']['must'].append({"terms": {"type": supported.split(',')}})
        if keyword: 
            query["bool"]["must"].append({
                "bool":{
                    "should":[
                        {"match": {"name": keyword}},
                        {"match": {"remark": keyword}},
                    ],
                    "minimum_should_match": 1
                }
            })
            sort_list                   = []
        list,total                      = await EFile.search(query=query,track_total_hits=10000,sort=sort_list,**{'from':skip,'size':size})
        for i,e in enumerate(list):
            list[i]                     = e.desensitization()
        return {'list':list,'total':total},

    async def destroy(self):
        post                            = await self.get_post()
        file_id                         = post.get('file_id',None)
        url                             = post.get('url',None)
        if file_id:
            efile                       = await EFile.afrom(file_id)
        elif url:
            efile                       = await EFile.afrom(url=url)
        else:
            return {},'无效的参数',0
        if efile==None:
            return {},'找不到该文件',404
        if efile.organization_id:
            if not await EOrganizationUser.afrom(organization_id=efile.organization_id,user_id=self.user._id):
                raise CodeError('无权限删除',403)
        elif efile.user_id != self.user._id:
            return {},'无权限删除',403
        await efile.destroy()
        return {},'删除成功'