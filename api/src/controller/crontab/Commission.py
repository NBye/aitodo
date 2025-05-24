from quart import request
from src.super.controllers import ContableController
from src.utils.errors import CodeError
from src.utils.funcs import log
import traceback,re

from src.entity.EOrganizationUser import EOrganizationUser
from src.entity.EOrganization import EOrganization
from src.entity.ECommissionBill import ECommissionBill

class Commission(ContableController):

    async def bill_generate(self):
        organization_id                 = request.args.get('organization_id')
        month                           = request.args.get('month')
        total,month                     = await ECommissionBill.refresh(
            organization_id             = organization_id,
            month                       = month
        )
        return {'total':total},month
        
