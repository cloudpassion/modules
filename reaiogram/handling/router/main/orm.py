from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger

from ....utils.enums import UPDATE_TYPES, MESSAGE_UPDATE_TYPES
from ....default.router import Router
from ....default.bot import Bot


async def update_to_orm(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event,
        #Message,
        data: Dict[str, Any]
) -> Any:

    # logger.info(f'-----------------update_to_orm-------------------------')
    logger.info(f'---------------------now-ret---------------------------')

    return await handler(event, data)
    # return await handler(event, data)

    event_update = data['event_update']
    bot = data['bot']
    dp = bot.dp

    merged_message = data.get('merged_message')

    me = await bot.me()
    orm = await dp.orm.bot_to_orm(bot=me)
    merged_bot = orm['merged_bot']

    logger.info(f'{merged_bot=}')
    logger.info(f'{merged_message=}')

    await dp.orm.update_to_orm(
        update=event_update, merged_bot=merged_bot,
        **{k: merged_message for k in MESSAGE_UPDATE_TYPES},
        **{k: data.get(f'merged_{k}') for k in UPDATE_TYPES if k not in MESSAGE_UPDATE_TYPES},
    )

    return await handler(event, data)


def register_update_to_orm_router(router):

    orm_router = Router(name='orm_router')

    for msg_type in UPDATE_TYPES:
        # logger.info(f'msg:{msg_type=}')
        router_msg = getattr(orm_router, msg_type)
        router_msg.outer_middleware.register(update_to_orm)

    router.include_router(orm_router)
