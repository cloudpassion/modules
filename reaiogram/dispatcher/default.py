import asyncio
import redis

from typing import Union

from aiogram import Dispatcher as DefaultDispatcher
from aiolimiter import AsyncLimiter

from config import secrets
from log import logger

from ..observer.event import EventObserver
from ..observer.telegram import TelegramEventObserver
from ..default.router import Router
from ..db import MyDjangoORM
from ..default.bot import Bot


class ExtraDispatcher(DefaultDispatcher):

    registered_handlers = set()
    orm: Union[
        MyDjangoORM, None
    ] = None

    bot: Bot
    bots: list

    router: Router
    event_observer: EventObserver
    telegram_event_observer: TelegramEventObserver

    async def init_database(self, db_class):

        logger.info(
            f'-------db: {db_class}\n'
            f'---------------------------------------------------------------'
        )
        self.orm = db_class()

        if isinstance(self.orm, MyDjangoORM):
            await self.orm.create(
                host=secrets.db.host, database=secrets.db.name,
                user=secrets.db.user, password=secrets.db.password,
                port=secrets.db.port

            )
            while not self.orm.pool:
                logger.info(f'wait {self.orm.pool=}')
                await asyncio.sleep(1)

    # this
    async def _append_handler_zzzzzzzzzz(self):
        pass
        # handler for checking all other
        # dispatcher handlers executed
        # TODO: rewrite to class as writed in DOCS
        # @self.message()
        # async def last_handler(*args, **kwargs):
        #     logger.info(f'last_handler')

    async def aextra(self):

        # handlers
        for key in dir(self):
            if '_append_handler_' in key:

                handler_name = '_'.join(key.split('_')[3:])
                if handler_name not in self.registered_handlers:
                    method = getattr(self, key)

                    logger.info(f'load handler: {handler_name}: {method}')
                    await method()
                    self.registered_handlers.add(handler_name)
                else:
                    logger.info(f'duplicate handler: {handler_name}')

        for key in dir(self):

            if '_aextra_' in key:
                method = getattr(self, key)
                logger.info(f'run {method=}')
                await method()
