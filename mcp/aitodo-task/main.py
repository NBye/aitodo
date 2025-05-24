from typing import Any
import httpx,json,os
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import asyncio

mcp = FastMCP("aitodo-task")

class TaskAttrs(BaseModel):
    title               : str           = Field(default="", description="任务标题")
    description         : str           = Field(..., description="任务描述")
    executor_user_id    : str           = Field(..., description="执行者的user_id")

    schedule_time       : str           = Field(..., description="计划执行时间，默认当前时间,")
    cron_enabled        : bool          = Field(default=False, description="是否开启周期计划")
    cron_expr           : str           = Field(default="* * * * *", description="周期执行计划，linux crontab 表达式的语法，不包含执行脚本部分")

@mcp.tool()
async def task_create(attrs:TaskAttrs) -> str:
    """创建任务"""
    token                               = os.getenv('AITODO_APIKEY')
    host                                = os.getenv('AITODO_HOST')
    headers                             = {
        "Authorization"                 : f"Bearer {token}",
        "Content-Type"                  : "application/json; charset=utf-8",
    }
    async with httpx.AsyncClient() as client:
        response                        = await client.post(
            f"{host}/open/task/create",
            headers                     = headers,
            json                        = attrs.model_dump(),
            timeout                     = 10
        )
    return response.text

if __name__ == "__main__":
    mcp.run(transport='stdio')

    