from src.super.controllers import BaseController

from src.utils.errors import CodeError

import config

class Constant(BaseController):

    async def templates(self):
        return {
            'definition'                : config.TEMPLATE_DEFINITION.strip(),
            'related_me'                : config.TEMPLATE_RELATED_ME.strip(),
            'understand'                : config.TEMPLATE_UNDERSTAND.strip(),
            'embeddings'                : config.TEMPLATE_EMBEDDINGS.strip(),
            'checkreply'                : config.TEMPLATE_CHECKREPLY.strip(),
            'recprompts'                : config.TEMPLATE_RECPROMPTS.strip(),
        },
        