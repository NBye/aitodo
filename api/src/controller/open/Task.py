from src.super.controllers import OpenController

from src.entity.ETask import ETask
from src.entity.EOrganization import EOrganization
from src.entity.EUser import EUser

from src.utils.errors import CodeError

class Task(OpenController):

    async def create(self):
        data                            = await self._check_data(None,[
            ('title',                   [0,200],     None,   '描述需要0~200个文字'),
            ('description',             [2,2000],    None,   '请输入有效的时间字符串'),
            ('executor_user_id',        [10,50],     None,   '执行者ID必传'),
            ('cron_enabled',            [0,50],      None,   '计划开启'),
            ('cron_expr',               [0,50],      None,   '计划'),
            ('schedule_time',           [0,50],      None,   '时间'),
        ])
        executor                        = await EUser.afrom(_id=data['executor_user_id'])
        if not executor:
            raise CodeError('找不到执行者:' + data['executor_user_id'])
        task                            = await ETask.create(user=self.user,executor=executor,organization=self.organization,refresh=True,**data)
        return {'task':task},'创建成功',
