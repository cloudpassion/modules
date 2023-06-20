from typing import Any

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger


async def simple_update(update: Update, **kwargs: Any) -> Any:
    if settings.tlog.enable and settings.tlog.simple.observer.telegram:
        logger.info(f'simple_update')

    raise SkipHandler()


# router at 19.06.2023 din not handling update and error
#
# INTERNAL_UPDATE_TYPES: Final[frozenset[str]] = frozenset({"update", "error"})
# skip_events = {*skip_events, *INTERNAL_UPDATE_TYPES}
def register_simple_telegram_event_observer(dp):

    # dp.update.register(simple_update)
    # router = Router(name='simple_router')

    # observer = dp.update
    # observer = TelegramEventObserver(
    #     router=dp,
    #     event_name='update',
    # )
    # observer.left_register(
    #     simple_update
    # )

    dp.update.register(simple_update)
    logger.info(f'{dp.update.handlers=}')

