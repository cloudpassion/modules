import re
import random
import asyncio

from typing import List
from aiolimiter import AsyncLimiter
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

from log import logger

from ..default.bot import Bot
from .default import ExtraDispatcher
from ..loader.setup import API_TOKEN


class NewBotDispatcher(
    ExtraDispatcher,
):

    upload_bot: Bot
    upload_bots: List[Bot]
    upload_sem = asyncio.Semaphore(5)
    upload_close = AsyncLimiter(1, time_period=60*1)
    upload_close_wait = False

    upload_at_minute = AsyncLimiter(40)
    upload_at_second = AsyncLimiter(1, time_period=2)

    def _new_bot(self):
        # bot = Bot(self.bot.token, parse_mode="HTML")
        bot = Bot(API_TOKEN, parse_mode="HTML")
        # self.upload_bot = bot
        return bot

    async def get_upload_bot(self):
        try:
            return self.upload_bots.pop()
        except IndexError:
            pass

        bot = self._new_bot()
        self.upload_bots.append(bot)
        return bot

    async def put_upload_bot(self, bot):
        self.upload_bots.append(bot)

    async def new_upload_bot(self, bot):

        try:
            self.upload_bots.pop(self.upload_bots.index(bot))
        except IndexError:
            pass

        await asyncio.sleep(random.randint(1, 10))

        while self.upload_close_wait:
            await asyncio.sleep(10)

        if self.upload_bots:
            logger.info(f'ret')
            return await self.get_upload_bot()

        self.upload_close_wait = True

        logger.info(f'old bot {bot=} close, {len(self.upload_bots)=}')
        async with self.upload_close:

            # self.upload_close_wait = True

            while True:
                await asyncio.sleep(1)
                try:
                    cl = await bot.close()
                    logger.info(f'{cl=}')
                    break
                except (
                        TelegramRetryAfter, TelegramBadRequest
                ) as exc:
                    try:
                        tm = int(re.findall('Retry in (.*?) seconds', f'{exc}')[0])
                    except Exception:
                        tm = 60

                    await asyncio.sleep(tm+random.randint(10, 20))
                except Exception as exc:
                    logger.info(f'{exc=}')
                    await asyncio.sleep(tm+random.randint(10, 20))

        bot = await self.get_upload_bot()
        self.upload_close_wait = False
        return bot

    async def _aextra_new_bot(self):
        self.upload_bot = self._new_bot()
        self.upload_bots = []
