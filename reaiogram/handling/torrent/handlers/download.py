import re
import asyncio
import random

from aiogram import F
from aiogram.handlers import BaseHandler
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

from config import secrets
from log import logger

from ...torrent.router import torrent_bot_router
from ....types.torrent.torrent import TorrentFile


@torrent_bot_router.message(
    F.message_thread_id == secrets.bt.chat.download.thread_id
)
class TorrentDownloadHandler(BaseHandler):
    async def handle(self):

        bot = self.bot
        dp = self.bot.dp

        data = self.data

        torrent: TorrentFile = data.get('torrent')

        if not torrent:
            return

        self.event: Message

        torrent_status = dp.torrents[torrent.info_hash]

        if torrent_status.in_work:
            return

        torrent_status.in_work = True

        try:
            cmt = torrent.comment or torrent.publisher_url
            if not cmt:
                cmt = ''

            while True:
                try:
                    await self.event.reply(
                        text=f'{torrent.name}\n'
                             f'{cmt}\n'
                             f'{torrent.info_hash}'
                    )
                    break
                except (
                    TelegramRetryAfter, TelegramBadRequest
                ) as exc:
                    tm = bot.get_retry_timeout(exc)

                    await asyncio.sleep(tm+random.randint(0, 5))

        except Exception as exc:
            logger.info(f'{exc=}')
            pass

        # def reply_callback():
        #     return self.event.reply(
        #         text=f'{torrent.name}\n'
        #              f'{torrent.info_hash}\n\n'
        #              f'complete'
        #     )
        # ret = reply_callback()
        # logger.info(f'{ret=}')

        asyncio.create_task(
            torrent.download_some_pieces(
                version=6,
                callback=self.event
            )
        )


def _():
    return