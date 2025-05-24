from src.entity.EChatMessage import EChatMessage
from src.entity.EOrganization import EOrganization
from src.entity.EUser import EUser

from src.utils.model.bailian.Chat import send

async def generate(model:str, organization:EOrganization,user:EUser,prompt='',messages:list[EChatMessage]=[],stream:bool=False,**options):
    async for data in send(model=model,messages=[
        *messages,
        *([await EChatMessage.virtual(content=prompt)] if prompt else []),
    ],organization=organization,user=user,stream=stream,**options):
        yield data
