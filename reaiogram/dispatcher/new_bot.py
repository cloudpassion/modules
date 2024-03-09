import re
import time
import random
import asyncio

from typing import List, Dict
from aiolimiter import AsyncLimiter
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession

from log import logger
from config import secrets

from ..default.bot import Bot
from .default import ExtraDispatcher
from ..loader.setup import API_TOKEN
from ..utils.scripts.http_session import create_http_session
from ..utils.enums import MAX_FILE_SIZE




if MAX_FILE_SIZE == 20971520:
    MAX_UPLOAD_SEM = 8
elif MAX_FILE_SIZE == 52428800:
    MAX_UPLOAD_SEM = 4


UPLOAD_BOTS = secrets.tg.upload_bots
OTHER_BOTS = secrets.tg.other_bots
MAX_UPLOAD_SEM = len(UPLOAD_BOTS)


class NewBotDispatcher(
    ExtraDispatcher,
):

    bots_data: Dict
    wait_upload = 0
    upload_bot: Bot
    upload_bots: List[Bot]
    upload_sem = asyncio.Semaphore(MAX_UPLOAD_SEM)
    upload_close = AsyncLimiter(1, time_period=10)
    upload_close_wait = False

    upload_at_minute = AsyncLimiter(60*len(UPLOAD_BOTS))
    upload_at_second = AsyncLimiter(len(UPLOAD_BOTS), time_period=1)

    def _new_bot(
            self,
            bot_name=None,
            token=None,
            proxy=None,
            bot=None,
            not_upload=False,
    ):

        if not bot_name and not token and not bot:
            raise Exception('no bot data')

        if bot:
            bot_name = bot._bot_name
            proxy = bot._proxy
            token = self.bots_data[bot_name]['token']

        if not token:
            token = self.bots_data[bot_name]['token']
            proxy = self.bots_data[bot_name]['proxy']

        # bot = Bot(self.bot.token, parse_mode="HTML")
        if proxy:
            session=create_http_session(proxy=proxy)
        else:
            session = None

        if bot:
            try:
                del self.upload_bots[self.upload_bots.index(bot)]
            except IndexError:
                pass

        bot = Bot(
            token,
            session=session,
            # parse_mode="HTML",
        )

        setattr(bot, 'dp', self)
        setattr(bot, '_bot_name', bot_name)
        setattr(bot, '_proxy', proxy)
        setattr(bot, 'wait_until', int(time.strftime('%s')))

        if not self.bots_data.get(bot_name):
            self.bots_data[bot_name] = {
                'token': token,
                'proxy': proxy,
                'id': bot.id,
            }

        if not not_upload:
            self.upload_bots.append(bot)

        return bot

    async def bot_update_wait(self, bot, time_to_wait):

        tm = int(time.strftime('%s'))
        setattr(bot, 'wait_until', tm + time_to_wait + 1)

    async def get_upload_bot(self, bot=None, time_to_wait=None):

        if bot and time_to_wait:
            await self.bot_update_wait(bot=bot, time_to_wait=time_to_wait)

        while True:

            upload_bots = self.upload_bots.copy()

            random.shuffle(upload_bots)

            tm = int(time.strftime('%s'))

            while upload_bots:

                bot = upload_bots.pop()

                wait_until: int = bot.wait_until

                if tm > wait_until:
                    break

            else:
                await asyncio.sleep(1)
                continue

            break

        return bot

    # async def put_upload_bot(self, bot):
    #     # try:
    #     #     bot.session.close()
    #     # except Exception as exc:
    #     #     logger.info(f'{exc=}')
    #
    #     try:
    #         await bot.session.close()
    #         try:
    #             del bot.session
    #         except Exception as exc:
    #             logger.info(f'{exc=}')
    #
    #         try:
    #             del bot
    #         except Exception as exc:
    #             logger.info(f'{exc=}')
    #
    #     except Exception as exc:
    #         logger.info(f'{exc=}')
    #
    #     #self.upload_bots.append(bot)

    async def new_upload_bot(self, bot):

        bot = self._new_bot(bot=bot)
        # try:
        #     self.upload_bots.pop(self.upload_bots.index(bot))
        # except (IndexError, ValueError):
        #     pass

        # await self.put_upload_bot(bot)
        return await self.get_upload_bot(bot=bot)

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
        # self.upload_bot = self._new_bot()
        self.upload_bot = None
        self.upload_bots = []
        self.bots_data = {}

        async def get_bot(bot_name, **kwargs):

            tg_data = getattr(secrets, 'tg')
            bot_data = getattr(tg_data, bot_name)
            token = getattr(bot_data, 'token')
            proxy = getattr(bot_data, 'proxy')

            _bot = self._new_bot(
                bot_name=bot_name,
                token=token,
                proxy=proxy,
                bot=None,
                **kwargs,
            )

            await _bot.me_orm()

            print(f'{_bot.id}')


        for _bot_name in UPLOAD_BOTS:
            await get_bot(_bot_name)


        for _bot_name in OTHER_BOTS:
            await get_bot(_bot_name, not_upload=True)

