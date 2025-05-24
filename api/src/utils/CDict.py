class CDict(dict):
    def __init__(self, *args, **kwargs):
        data                            = {}
        for o in [*args,kwargs]:
            data.update(o)
        for k,v in data.items():
            if isinstance(v, dict) and not isinstance(v, CDict):
                self[k]                 = CDict(v)
            else:
                self[k]                 = v
    def __getattr__(self, name):
        return self.get(name,None)
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        if key in self:
            del self[key]