from typing import Callable, Dict, Any, Awaitable

from aiogram import types
from aiogram import exceptions
from aiogram import BaseMiddleware

from aiogram.types import Message

from log import logger, log_stack
from config import secrets, settings

from ..dispatcher.default import DefaultDispatcher as Dispatcher

from ..db.schemas.django import MyDjangoORM


class DatabaseMiddleware(
    BaseMiddleware,
):

    async def _message_to_database(self, message):
        dispatcher = self.manager.dispatcher
        sql: MyDjangoORM = dispatcher.orm
        ret = await sql.database_message(message=message)
        if ret and isinstance(ret, dict):
            return ret

        return {}

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
    # async def on_post_process_message(
    #         self,
    #         message: types.Message, data: dict,
    #         *args
    # ):
        logger.info(f'{data=}')
        await self._message_to_database(event)

    # async def on_post_process_edited_message(
    #         self,
    #         message: types.Message, data: dict,
    #         *args
    # ):
    #     logger.info(f'{data=}')
    #     await self._message_to_database(message)


def register_database_middleware(dp):
    logger.info(f'{dp=}, {dir(dp)}')
    dp.middleware.setup(DatabaseMiddleware())
