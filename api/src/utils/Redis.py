import config
import redis.asyncio as redis


POOL                                    = redis.ConnectionPool(**config.REDIS_OPTIONS)
SCENE_MAP                               = {
    'user'                              : 6,
    'organization'                      : 8,
    'organization_event'                : 7,
    'task'                              : 7,
}
class Redis():
    def __init__(self,scene=None):
        if scene and SCENE_MAP.get(scene,None):
            db                          = SCENE_MAP[scene]
        else:
            db                          = config.REDIS_OPTIONS['db']
        self._r                         = redis.Redis(connection_pool=POOL,db=db)

    def __getattr__(self, name):
        return getattr(self._r, name)
