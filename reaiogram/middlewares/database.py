from typing import Callable, Dict, Any, Awaitable

from aiogram import types
from aiogram.utils import exceptions
from aiogram.dispatcher.middlewares import BaseMiddleware

from log import logger, log_stack
from config import secrets, settings

from ..dispatcher.default import DefaultDispatcher as Dispatcher

from ..db.schemas.django import MyDjangoORM


class DatabaseMiddleware(
    BaseMiddleware,
):

    async def _message_to_database(self, message):
        dispatcher = self.manager.dispatcher
        sql: MyDjangoORM = dispatcher.sql
        ret = await sql.database_message(message=message)
        if ret and isinstance(ret, dict):
            return ret

        return {}

    async def on_post_process_message(
            self,
            message: types.Message, data: dict,
            *args
    ):
        logger.info(f'{data=}')
        await self._message_to_database(message)

    async def on_post_process_edited_message(
            self,
            message: types.Message, data: dict,
            *args
    ):
        logger.info(f'{data=}')
        await self._message_to_database(message)


def register_database_middleware(dp):
    dp.middleware.setup(DatabaseMiddleware())
