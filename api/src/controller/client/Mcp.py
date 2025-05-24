import os,json,aiofiles,traceback

from src.super.controllers import OrganizationController

from src.utils.errors import CodeError
from src.utils.funcs import log

import config

class Mcp(OrganizationController):

    async def search(self):
        list                            = []
        for entry in os.scandir(config.MCP_DIR):
            try:
                async with aiofiles.open(f"{config.MCP_DIR}/{entry.name}/config.json", mode='r') as f:
                    content             = await f.read()
                    setting             = json.loads(content)
                    setting['cwd']      = f"{config.MCP_DIR}/{entry.name}"
                    list.append(setting)
            except Exception as e:
                await log(f'{e}\n{traceback.format_exc()}')
        return {'list':list},

    async def info(self):
        pass