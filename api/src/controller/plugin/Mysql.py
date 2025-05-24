import json,sys
import pymysql
import aiomysql
import config
from datetime import datetime

from src.super.controllers import PluginController
from src.utils.errors import CodeError 
from src.entity.EDataBase import EDataBase 

class Mysql(PluginController):
    
    async def _exec_sql(self,sql,chat=None):
        if not chat:
            chat                        = await self.current_chat()
        connect_data                    = {
            'host'                      : chat.metadata.get('host',None),
            'port'                      : chat.metadata.get('port',None),
            'user'                      : chat.metadata.get('user',None),
            'password'                  : chat.metadata.get('password',None),
            'db'                        : chat.metadata.get('database',None),
        }
        async with aiomysql.create_pool(**connect_data) as pool:
            async with pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    rows            = await cursor.fetchall()
                    return [row for row in rows]

    async def connect(self):
        post                            = await self.get_post()
        hostname                        = post.get('host')
        username                        = post.get('username','root')
        userpass                        = post.get('userpass')
        port                            = post.get('port',3306)
        database                        = post.get('database','test')
        chat                            = await self.current_chat()
        if not hostname or not username or not userpass:
            raise CodeError('请输入有效的Mysql连接参数')
        connection,cursor,data          = None,None,{'db_list':[],'dbname':database}
        metadata                        = chat.metadata or {}
        metadata.update(
            host                        = hostname,
            user                        = username,
            password                    = userpass,
            port                        = port,
            database                    = database,
        )
        db_list                         = await self._exec_sql('SHOW DATABASES')
        await chat.upset(metadata=metadata)
        return {'db_list':db_list},f'数据库连接成功，当前数据库: {database}'

    async def switchdb(self):
        post                            = await self.get_post()
        dbname                          = post.get('dbname')
        for item in await self._exec_sql('SHOW DATABASES'):
            if dbname==item['Database']:
                chat                    = await self.current_chat()
                metadata                = chat.metadata or {}
                metadata.update(database=dbname)
                await chat.upset(metadata=metadata)
                return {},f'切换成功,当前数据库为: {dbname}'
        return {},f'当前连接没有数据: {dbname}'

    async def dbcreate(self):
        post                            = await self.get_post()
        dbname                          = post.get('dbname')
        charset                         = post.get('charset','utf8mb4')
        if not dbname or not charset:
            raise CodeError('请输入有效的创建数据库参数')
        return {
            'dbname'                    : dbname,
            'charset'                   : charset,
        },

    async def query(self):
        post                            = await self.get_post()
        sql                             = post.get('sql')
        list                            = []
        for item in await self._exec_sql(sql):
            list.append(item)
        return {'list':list},f'查询成功'