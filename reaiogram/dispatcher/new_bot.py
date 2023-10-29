import re
import random
import asyncio

from typing import List
from aiolimiter import AsyncLimiter
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession

from log import logger

from ..default.bot import Bot
from .default import ExtraDispatcher
from ..loader.setup import API_TOKEN
from ..utils.scripts.http_session import create_http_session


class NewBotDispatcher(
    ExtraDispatcher,
):

    wait_upload = 0
    upload_bot: Bot
    upload_bots: List[Bot]
    upload_sem = asyncio.Semaphore(4)
    upload_close = AsyncLimiter(1, time_period=10)
    upload_close_wait = False

    upload_at_minute = AsyncLimiter(60)
    upload_at_second = AsyncLimiter(1, time_period=1)

    def _new_bot(self):
        # bot = Bot(self.bot.token, parse_mode="HTML")
        bot = Bot(
            API_TOKEN,
            # parse_mode="HTML",
            # session=create_http_session()
        )
        setattr(bot, 'dp', self)
        # self.upload_bot = bot
        return bot

    async def get_upload_bot(self):
        try:
            return self.upload_bots.pop()
        except IndexError:
            pass

        bot = self._new_bot()
        #self.upload_bots.append(bot)
        return bot

    async def put_upload_bot(self, bot):
        # try:
        #     bot.session.close()
        # except Exception as exc:
        #     logger.info(f'{exc=}')

        try:
            await bot.session.close()
            try:
                del bot.session
            except Exception as exc:
                logger.info(f'{exc=}')

            try:
                del bot
            except Exception as exc:
                logger.info(f'{exc=}')

        except Exception as exc:
            logger.info(f'{exc=}')

        #self.upload_bots.append(bot)

    async def new_upload_bot(self, bot):

        # try:
        #     self.upload_bots.pop(self.upload_bots.index(bot))
        # except (IndexError, ValueError):
        #     pass

        await self.put_upload_bot(bot)
        return await self.get_upload_bot()

        await asyncio.sleep(random.randint(1, 10))

        while self.upload_close_wait:
            await asyncio.sleep(10)

        # if self.upload_bots:
        #     # logger.info(f'ret')
        #     return await self.get_upload_bot()

        self.upload_close_wait = True

        # logger.info(f'old bot {bot=} close, {len(self.upload_bots)=}')
        # async with self.upload_close:
        # self.upload_close_wait = True

        while True:
            try:

                # async with bot.session.close:
                #     await asyncio.sleep(0)

                bot: Bot
                session: AiohttpSession = bot.session
                await session.close()
                #logger.ianfo(f'{session=}\n\n\n\n\n')
                #del session
                del bot.session
                del bot
                # await bot.session.close()
                #logger.info(f'cl')

                break
            except Exception as exc:
                logger.info(f'{exc=}')
                await asyncio.sleep(30+random.randint(10, 20))

        bot = await self.get_upload_bot()
        self.upload_close_wait = False
        return bot

    async def _aextra_new_bot(self):
        self.upload_bot = self._new_bot()
        self.upload_bots = []
