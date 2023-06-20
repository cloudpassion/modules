from ..default.bot import Bot
from ..dispatcher import Dispatcher

from ..types.tg.bot import MergedTelegramBot


async def get_updates(
        dispatcher: Dispatcher, bot: Bot
):

    me = await bot.me()

    merged_bot = MergedTelegramBot(dispatcher.orm, bot=me)
    await merged_bot.merge_bot()

    last_update = await dispatcher.orm.select_tg_last_update(
        bot=merged_bot
    )

    if not last_update:
        last_id = 0
    else:
        last_id = last_update.id

    await bot.get_updates(
        offset=last_id+1
    )
