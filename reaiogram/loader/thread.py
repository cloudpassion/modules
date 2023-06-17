import asyncio
import threading

from time import sleep
from aiogram import Bot
from aiogram import types
from aiogram import executor
from aiogram.bot.api import TelegramAPIServer

from reaiogram.dispatcher import ThreadDispatcher as Dispatcher
from reaiogram.storage import MainStorage
from log import mlog
from . import API_TOKEN, pollbot_proxy, sendbot_proxy,\
    register_middlewares, register_dialogs, register_filters, register_handlers, \
    register_webhook, WEBHOOK, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, \
    API_URL


class Monitor:

    def __init__(
            self, polling_bot, dispatcher,
            storage,
            on_startup, on_shutdown,
    ):
        self._polling_bot = polling_bot
        self._dispatcher = dispatcher
        self.storage = storage
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown

        self.dispatcher = None
        self.polling_bot = None
        self.dp_loop = None
        self.dp_thread = None

    def run_threads(self):

        # back to dp loop

        self.dp_loop = asyncio.get_event_loop()

        _dp_thread = threading.Thread(
            target=self.dispatcher_forever,
            args=(self._dispatcher, )
        )
        _dp_thread.start()

        self.dp_thread = _dp_thread

        # sql loop

        #_sql_loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(_sql_loop)
        #sql = None
        #self.sql_loop = _sql_loop

        # sql
        # dispacher
        #

    def dispatcher_forever(self, dp):
        asyncio.set_event_loop(self.dp_loop)
        mlog.info(f'dp_forever: {dp}')

        self.polling_bot = self._polling_bot(
            token=API_TOKEN,
            proxy=pollbot_proxy.proxy,
            proxy_auth=pollbot_proxy.aiogram_auth,
            parse_mode=types.ParseMode.HTML,
            server=TelegramAPIServer.from_base(API_URL)
        )
        self.dispatcher = dp(
            self.polling_bot,
            storage=self.storage,
        )

        register_webhook(self.polling_bot)
        register_middlewares(self.dispatcher)
        register_dialogs(self.dispatcher)
        register_filters(self.dispatcher)
        register_handlers(self.dispatcher)

        if not WEBHOOK:
            executor.start_polling(
                self.dispatcher, skip_updates=True,
                on_startup=self.on_startup, on_shutdown=self.on_shutdown,
            )
        else:
            executor.start_webhook(
                self.dispatcher,
                webhook_path=WEBHOOK_PATH, check_ip=True,
                skip_updates=True,
                on_startup=self.on_startup, on_shutdown=self.on_shutdown,
            )


def thread_loader(on_startup, on_shutdown):

    polling_bot = Bot

    storage = MainStorage

    mon = Monitor(
        polling_bot=polling_bot,
        dispatcher=Dispatcher,
        storage=storage,
        on_startup=on_startup, on_shutdown=on_shutdown,
    )

    mon.run_threads()
