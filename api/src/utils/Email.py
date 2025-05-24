from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from src.utils.errors import CodeError

from aiosmtplib import send

import config

class Email():
    def __init__(self,sender=None, auth=None, smtp=None, port=None):
        self.sender                     = sender    or config.EMAIL_SENDER
        self.auth                       = auth      or config.EMAIL_AUTH
        self.smtp                       = smtp      or config.EMAIL_SMTP
        self.port                       = port      or int(config.EMAIL_PORT)
        if not self.auth or not self.smtp or not self.port:
            raise CodeError('未配置SMTP邮箱参数')
        

    async def send(self, email, subject, body,label=None, format='html', charset='utf8'):
        message                         = MIMEText(body, format, charset)
        message["From"]                 = Header(formataddr((label or config.EMAIL_LABEL, self.sender)))
        message["To"]                   = Header(email)
        message["Subject"]              = Header(subject, charset)
        await send(message, hostname=self.smtp, port=self.port, username=self.sender, password=self.auth, start_tls=True)
        return True
