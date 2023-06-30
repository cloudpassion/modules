import os
import asyncio
import django

from typing import Any
from aiohttp.web import Application
from aiogram import enums

from aiogram.client.telegram import TelegramAPIServer

from config import secrets
from log import logger

from ..default.aiohttp.session import AiohttpSession
from ..default.storage import MainStorage
from ..default.router import Router
from ..default.bot import Bot
from ..dispatcher import Dispatcher

from ..utils.help.router import RouterHelp

from .register import (
    register_observers,
    register_middlewares,
    register_routers,
)

from .setup import (
    API_TOKEN,
    API_TOKENS,
    API_BASE_URL, API_FILE_URL,
)

from .on_startup import _run_on_startup
from .on_shutdown import _run_on_shutdown


async def default_loader():

    # TODO: fix proxy here
    # auth = BasicAuth(login="user", password="password")
    # session = AiohttpSession(proxy=("protocol://host:port", auth))
    # proxy = ("protocol://host:port", auth)
    # "protocol://user:password@host:port"
    api_session = AiohttpSession(
        # proxy=f'http://{secrets.proxy.http.ip}:{secrets.proxy.http.port}',
        proxy=None,
        api=TelegramAPIServer(
            base=API_BASE_URL,
            file=API_FILE_URL,
        ),
    )

    bots = []
    for api_token in API_TOKENS:
        bot = Bot(
            token=api_token,
            parse_mode=enums.ParseMode.HTML,
            session=api_session,
        )
        bots.append(bot)

    storage = MainStorage

    dp = Dispatcher(
        storage=storage,
    )

    for bot in bots:
        setattr(bot, 'dp', dp)

    # on_event
    dp.startup.register(_run_on_startup)
    dp.shutdown.register(_run_on_shutdown)

    # register handlers
    register_middlewares(dp)
    register_observers(dp)

    register_routers(dp)

    RouterHelp().list_routers(dp)

    return bots, dp
