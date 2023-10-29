import redis
import random
import asyncio

from surge.metadata import (
    yield_available_pieces,
)

from log import logger


async def redis_memory_wait(
        r: redis.Redis,
        more_total,
        max_memory=None,
        first_sleep=150,
        info=''
):

    total = int(r.memory_stats()['total.allocated'])
    # logger.info(f'{total=}, {max_memory=}')
    if not max_memory:
        max_memory = int(r.config_get('maxmemory')['maxmemory'])

    while total + more_total > max_memory:
        logger.info(f'wait for free memory, {info=}')
        await asyncio.sleep(first_sleep+random.randint(10, 20))
        total = int(r.memory_stats()['total.allocated'])


class TorrentCheck:

    def yield_available_pieces(self, folder):
        return yield_available_pieces(self.metadata.pieces, folder, self.metadata.files)


