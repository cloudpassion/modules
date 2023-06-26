from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger

from reaiogram.dispatcher.default import ExtraDispatcher


class OuterMiddlewareDispatcher(ExtraDispatcher):

    async def _append_handler_0_outer_debug(self):

        @self.update.outer_middleware()
        async def outer_debug(
                handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
                event: Update,
                data: Dict[str, Any]
        ) -> Any:

            logger.info(f'-----------------outer_debug-------------------------')
            return await handler(event, data)

