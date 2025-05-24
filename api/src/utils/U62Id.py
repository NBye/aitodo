import time
import random

class U62Id():
    
    CHARS                               = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    @classmethod
    def encode(cls, num):
        if num == 0:
            return '0'
        result                          = ''
        while num > 0:
            result                      = cls.CHARS[num % 62] + result
            num                         //= 62
        return result

    @classmethod
    def decode(cls, string):
        result                          = 0
        length                          = len(string)
        for i in range(length):
            index                       = cls.CHARS.index(string[i])
            result                      = result * 62 + index
        return result

    @classmethod
    def generate(cls, length=32):
        prefix                          = cls.encode(int(time.time() * 1000))
        length                          = length-len(prefix)
        if length < 0:
            raise Exception(f'U62Id.generate length Need more than: {len(prefix)}')
        elif length==0:
            return prefix
        suffix                          = cls.encode(random.randint(0, cls.decode('Z'*length))).zfill(length)
        return prefix + suffix

        
        
        