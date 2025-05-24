class CodeError(Exception):
    def __init__(self, message, code=0,data={}):
        super().__init__(message)
        self.code = code
        self.data = data