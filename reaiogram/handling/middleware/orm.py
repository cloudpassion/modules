from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update, Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware


from log import logger


class OrmMessageMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):

        # logger.info(f'--------ret-message_to_orm--------')
        return await handler(event, data)
        logger.info(f'--------message_to_orm--------')
        event_router = data['event_router']
        # logger.info(f'{event=}')
        orm_ret = await event_router.orm.message_to_orm(event)
        data.update(orm_ret)
        return await handler(event, data)


def register_orm_middleware(dp):
    # dp.message.outer_middleware(OrmMessageMiddleware())
    # dp.edited_message.outer_middleware(OrmMessageMiddleware())
    # router = Router(name='next_update')
    # dp.update.middleware(NextUpdateHandler())
    return
