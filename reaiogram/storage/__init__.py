from aiogram.contrib.fsm_storage.memory import BaseStorage

from .memory import MemoryStorage, ThreadMemoryStorage
#from .mongo import MongoStorage, ThreadMongoStorage 29.08 not work bson
from .redis import RedisStorage, ThreadRedisStorage
from config import settings


__storage__ = {
    'None': None,
    'BaseStorage': BaseStorage(),
    'MemoryStorage': MemoryStorage(),
    #'MongoStorage': MongoStorage(),
    'RedisStorage': RedisStorage(),
    'ThreadMemoryStorage': ThreadMemoryStorage(),
    #'ThreadMongoStorage': ThreadMongoStorage(),
    'ThreadRedisStorage': ThreadRedisStorage(),
}

MainStorage = __storage__[settings.db.storage]