from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class NextUpdateHandler(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ):
        await handler(event, data)
        # raise SkipHandler()


def register_next_update_middleware(dp):
    # router = Router(name='next_update')
    # dp.update.middleware(NextUpdateHandler())
    return
