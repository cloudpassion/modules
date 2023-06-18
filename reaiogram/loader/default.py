import asyncio

from aiogram import Bot
from aiogram import types
from aiogram import enums
# from aiogram import executor
# from aiogram.bot.api import TelegramAPIServer
from aiogram.client.telegram import TelegramAPIServer

from reaiogram.dispatcher import Dispatcher
from reaiogram.storage import MainStorage
from . import API_TOKEN, pollbot_proxy, sendbot_proxy, \
    register_middlewares, register_dialogs, register_filters, register_handlers, \
    register_webhook, WEBHOOK, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, \
    API_URL


def default_loader(on_startup, on_shutdown):

    bot = Bot(
        token=API_TOKEN,
        #proxy=pollbot_proxy.proxy,
        #proxy_auth=pollbot_proxy.aiogram_auth,
        parse_mode=enums.ParseMode.HTML,
        # server=TelegramAPIServer.from_base(API_URL)
    )
    storage = MainStorage
    dp = Dispatcher(bot, storage=storage)

    register_webhook(bot)
    register_middlewares(dp)
    register_dialogs(dp)
    register_filters(dp)
    register_handlers(dp)

    if not WEBHOOK:
        asyncio.run(on_startup(dp))
        # asyncio.run(dp.skip_updates())
        asyncio.run(dp.start_polling(bot))
        asyncio.run(on_shutdown(dp))
        # executor.start_polling(
        #     dp, on_startup=on_startup, on_shutdown=on_shutdown,
        #     skip_updates=True,
        # )

    else:
        executor.start_webhook(
            dp,
            webhook_path=WEBHOOK_PATH, check_ip=True,
            skip_updates=True,
            on_startup=on_startup, on_shutdown=on_shutdown,
        )




