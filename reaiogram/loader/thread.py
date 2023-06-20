import time
import asyncio
import threading

from collections import deque

from log import logger

from .django_load import setup_django


class Monitor:

    tg_loop: asyncio.AbstractEventLoop
    bt_loop: asyncio.AbstractEventLoop
    tg_thread: threading.Thread

    # dp: Dispatcher
    # poll_bots: List[Bot, ]
    # poll_bot: Bot

    def __init__(self):
        self.timeline = deque()

    def run_threads(self):

        tg_loop = asyncio.new_event_loop()
        self.tg_loop = tg_loop
        _dp_thread = threading.Thread(
            target=self.poll_forever,
            args=(self.tg_loop, )
        )
        self.tg_thread = _dp_thread
        _dp_thread.start()

        # sql loop

        #_sql_loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(_sql_loop)
        #sql = None
        #self.sql_loop = _sql_loop

        # sql
        # dispacher
        #

    def poll_forever(self, tg_loop):
        logger.info(f'{tg_loop=}')
        asyncio.set_event_loop(tg_loop)
        asyncio.run(self.thread_loader())

    async def thread_loader(self):

        from .default import default_loader, Bot, Dispatcher
        bots, dp = await default_loader()

        self.poll_bots = bots
        self.poll_bot = bots[0]
        self.dp = dp

        from .setup import (
            WEBHOOK, WEBHOOK_SSL, WEBHOOK_URL
        )

        if not WEBHOOK:
            await dp.start_polling(
                *bots
            )
        else:
            for bot in bots:
                await bot.set_webhook(
                    url=WEBHOOK_URL,
                    certificate=WEBHOOK_SSL,
                )
            await dp.start_polling(
                *bots
            )
            logger.info(f'\n\n\n\n\n\nEXIT\n\n\n\n\n')


def run_thread():

    setup_django()

    mon = Monitor()
    mon.run_threads()

    while True:

        time.sleep(1)
        logger.info(f'thread sleep')
