from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger

from reaiogram.dispatcher.default import ExtraDispatcher


class OuterLogForDispatcher(ExtraDispatcher):

    async def _append_handler_001_outer_log(self):

        @self.update.outer_middleware()
        async def outer_log(
                handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
                event: Update,
                data: Dict[str, Any]
        ) -> Any:

            logger.info(f'-----------------incoming_log-------------------------')

            return await handler(event, data)

