from aiogram.fsm.storage.redis import RedisStorage as DefaultRedisStorage


class RedisStorage(DefaultRedisStorage): pass


class ThreadRedisStorage(DefaultRedisStorage): pass
