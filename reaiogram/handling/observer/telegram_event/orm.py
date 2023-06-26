from typing import Any, Dict, Awaitable, Callable

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler

from config import settings
from log import logger


from ....default.bot import Bot


async def save_update(
        update: Update,
        bot: Bot,
        **kwargs: Any,
) -> Any:

    raise SkipHandler()

    # dp = bot.dp
    #
    # data = {}
    # logger.info(f'-----------------save_update-------------------------')
    # me = await bot.me()
    #
    # # merged_message = data.get('merged_message')
    # # merged_bot = data.get('merged_message')
    #
    # orm = await dp.orm.bot_to_orm(bot=me)
    # merged_bot = orm['merged_bot']
    #
    # await bot.dp.orm.update_to_orm(
    #     update=update, merged_bot=merged_bot,
    # )
    #
    # raise SkipHandler()


def register_save_update_telegram_event_observer(dp):
    dp.update.register(save_update)
