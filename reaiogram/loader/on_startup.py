import asyncio

from typing import List
from log import logger

from ..db import DbClass

from ..default.bot import Bot

from .updates import get_updates


async def run_on_startup(
        dispatcher, bot: Bot, bots: List[Bot], **kwargs
):

    logger.info(f'{dispatcher=}, {bot=}, {kwargs=}')
    # await add_kafka_handler()
    # await set_default_commands(dispatcher)
    # await on_startup_notify(dispatcher)

    await dispatcher.init_database(DbClass)
    await dispatcher.aextra()

    # t = 0
    # while True:
    #     t += 1
    #     await asyncio.sleep(1)
    #     if t > 20:
    #         break

    for bt in bots:
        logger.info(f'{bt=}')

        asyncio.create_task(get_updates(dispatcher, bt))


        # await _bot.get_updates()t
    # for _bot in bots:
    #
    #     me = await bot.me()
    #     logger.info(f'{me=}')
    #     await dispatcher.orm.database_bot(
    #         bot=me
    #     )
