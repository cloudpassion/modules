from aiogram.types import Message
from aiogram.dispatcher.event.bases import SkipHandler

from ...dispatcher.default import ExtraDispatcher

from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger

from ...utils.enums import UPDATE_TYPES, MESSAGE_UPDATE_TYPES
from ...default.router import Router
from ...default.bot import Bot


class OrmDispatcher(ExtraDispatcher):

    async def _append_handler_020_orm(self):

        @self.update.outer_middleware()
        async def save_update_to_orm(
                handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
                update: Update,
                data: Dict[str, Any]
        ):

            logger.info(f'-----------------update_to_orm-------------------------')

            bot = data['bot']

            me = await bot.me()
            merged_bot = await bot.me_orm()

            await self.orm.update_to_orm(
                update=update, merged_bot=merged_bot,
            )

            return await handler(update, data)


