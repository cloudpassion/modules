from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler
# from aiogram.utils.mixins import ContextInstanceMixin
from config import settings
from log import logger


from ....default.bot import Bot


async def save_update(
        update: Update,
        bot: Bot,
        **kwargs: Any,
) -> Any:

    data = {}
    logger.info(f'-----------------save_update-------------------------')
    me = await bot.me()
    data.update(await bot.dp.orm.database_bot(bot=me))

    merged_bot = data['merged_bot']

    await bot.dp.orm.database_update(update=update, merged_bot=merged_bot)

    raise SkipHandler()


def register_save_update_telegram_event_observer(dp):
    dp.update.register(save_update)
