from typing import Any
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import asyncio

from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from aiosmtplib import send

mcp = FastMCP("email")

class SnedParams(BaseModel):
    email               : str           = Field(..., description="接收者邮箱")
    subject             : str           = Field(..., description="主题文案")
    body                : str           = Field(..., description="邮件正文")
    label               : str           = Field(default="", description="发送者Label")
    format              : str           = Field(default="html", description="邮件内容格式")
    charset             : str           = Field(default="utf8", description="邮件编码")

@mcp.tool()
async def send(params:SnedParams) -> str:
    """发送邮件"""
    USERLABEL                           = os.getenv('USERLABEL') or ''
    USERNAME                            = os.getenv('USERNAME') or ''
    PASSWORD                            = os.getenv('PASSWORD') or ''
    HOST_SMTP                           = os.getenv('HOST_SMTP') or ''
    HOST_PORT                           = os.getenv('HOST_PORT') or ''

    email                               = params.email
    subject                             = params.subject
    body                                = params.body
    label                               = params.label
    format                              = params.format
    charset                             = params.charset

    message                             = MIMEText(body, format, charset)
    message["From"]                     = Header(formataddr((label or USERLABEL, USERNAME)))
    message["To"]                       = Header(email)
    message["Subject"]                  = Header(subject, charset)
    await send(message, hostname=HOST_SMTP, port=HOST_PORT, username=USERNAME, password=PASSWORD, start_tls=True)
    return "发送成功"


if __name__ == "__main__":
    mcp.run(transport='stdio')