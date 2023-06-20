import os
import asyncio
import django

from aiogram import enums

from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession

from log import logger

from ..default.storage import MainStorage
from ..default.router import Router
from ..default.bot import Bot
from ..dispatcher import Dispatcher

from ..utils.help.router import RouterHelp

from .register import (
    register_observers,
    register_middlewares
)

from .setup import (
    API_TOKEN,
    API_TOKENS,
    API_BASE_URL, API_FILE_URL,
)

from .on_startup import run_on_startup
from .on_shutdown import run_on_shutdown


async def default_loader():

    # TODO: fix proxy here
    # auth = BasicAuth(login="user", password="password")
    # session = AiohttpSession(proxy=("protocol://host:port", auth))
    # proxy = ("protocol://host:port", auth)
    # "protocol://user:password@host:port"
    api_session = AiohttpSession(
        proxy=None,
        api=TelegramAPIServer(
            base=API_BASE_URL,
            file=API_FILE_URL,
        )
    )

    bots = []
    for api_token in API_TOKENS:
        bot = Bot(
            token=API_TOKEN,
            parse_mode=enums.ParseMode.HTML,
            session=api_session
        )
        bots.append(bot)

    storage = MainStorage

    dp = Dispatcher(
        storage=storage,
    )

    for bot in bots:
        setattr(bot, 'dp', dp)

    router = Router(name='main')
    dp.include_router(
        router=router,
    )
    # dp.set_extra(
    #     bots=bots,
    #     router=router,
    # )

    # on_event
    dp.startup.register(run_on_startup)
    dp.shutdown.register(run_on_shutdown)

    # register handlers
    register_middlewares(dp)
    register_observers(dp)

    RouterHelp().list_routers(dp)

    return bots, dp
