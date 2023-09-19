from typing import Dict, Any, Callable, Awaitable

from aiogram.types import Message, Update
from aiogram.enums.update_type import UpdateType
from aiogram.dispatcher.event.bases import SkipHandler, CancelHandler

from reaiogram.default.router import Router

from config import secrets
from log import logger


async def allow_creator(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
) -> Any:

    try:
        if event.from_user.id == secrets.rights.creator.id:
            logger.info(f'handle for creator')
            data.update({'rights_passed': True})

        # temp
        if event.from_user.id in [513231497, 995243063]:
            logger.info(f'handle for temp')
            data.update({'rights_passed': True})

    except Exception:
        logger.info(f'unparsed_type')

    return await handler(event, data)


async def stop_handling(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
) -> Any:

    if data.get('rights_passed'):
        logger.info('passed')
        return await handler(message, data)

    logger.info(f'stop. users not allowed')

    # return await handler(message, data)


async def test_handling(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
) -> Any:

    logger.info(f'after rejected')

    return await handler(message, data)


def register_rights_all(router):

    for msg_type in UpdateType:
        logger.info(f'{msg_type}')
        router_msg = getattr(router, msg_type)

        router_msg.outer_middleware.register(allow_creator)

        router_msg.outer_middleware.register(stop_handling)

        router_msg.outer_middleware.register(test_handling)
