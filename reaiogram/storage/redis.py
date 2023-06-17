from aiogram.contrib.fsm_storage.redis import RedisStorage2 as DefaultRedisStorage


class RedisStorage(DefaultRedisStorage): pass


class ThreadRedisStorage(DefaultRedisStorage): pass
