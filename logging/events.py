
import asyncio
from enum import Enum

class ResponseResult(Enum):
        SUCCESS = 1
        FAILURE = 0



class ResponseEvent(asyncio.Event):

    def __init__(self):
        super().__init__()
        self.response=None
        self.value=None
    
    async def wait(self):
        
        await super().wait()
        return self.response , self.value

    def set(self, response:ResponseResult, value=None):
        self.response=response
        self.value=value
        return super().set()

    def clear(self):
        self.response=None
        self.value=None
        return super().clear()
