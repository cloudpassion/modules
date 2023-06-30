import asyncio

from typing import Any, Dict, Awaitable, Callable
from aiogram.types import Update

from log import logger

from reaiogram.dispatcher.default import ExtraDispatcher


class OuterInitMiddlewareForDispatcher(ExtraDispatcher):

    async def _append_handler_000_outer_init(self):

        @self.update.outer_middleware()
        async def outer_debug(
                handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
                event: Update,
                data: Dict[str, Any]
        ) -> Any:

            logger.info(f'-----------------outer_init-------------------------')
            return await handler(event, data)

