from datetime import datetime

from src.utils.errors import CodeError 

class Datetime(datetime):

    @classmethod
    def afrom(cls, value=None,format="%Y-%m-%d %H:%M:%S"):
        if value == None:
            value = datetime.now()
            return cls(value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond)
        elif isinstance(value,datetime):
            return cls(value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond)
        elif isinstance(value,str):
            value = datetime.strptime(value, format)
            return cls(value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond)
        else:
            raise CodeError('Datetime aform Error！')

    def format(self,format="%Y-%m-%d %H:%M:%S"):
        return self.strftime(format)