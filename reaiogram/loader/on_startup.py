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

    for bt in bots:
        logger.info(f'{bt=}')

        asyncio.create_task(get_updates(dispatcher, bt))
        asyncio.create_task(bt.me())
