from typing import Any

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger


async def log_update(update: Update, **kwargs: Any) -> Any:
    logger.info(f'---------------------log_update----------------------------')
    # logger.info(f'{kwargs=}')
    # logger.info(f'{update=}')
    raise SkipHandler()


def register_log_update_telegram_event_observer(dp):
    dp.update.register(log_update)
