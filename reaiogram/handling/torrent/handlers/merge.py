import asyncio

from aiogram import F
from aiogram.handlers import BaseHandler

from config import secrets
from log import logger

from ...torrent.router import torrent_bot_router
from ....types.torrent.torrent import TorrentFile


@torrent_bot_router.message(
    F.message_thread_id == secrets.bt.chat.merge.thread_id
)
class TorrentMergeHandler(BaseHandler):
    async def handle(self):

        dp = self.bot.dp

        data = self.data

        torrent: TorrentFile = data.get('torrent')

        dp.torrent[torrent.info_hash] = True

        if not torrent:
            return

        await torrent.grab_torrent_from_telegram(version=6)
        # asyncio.create_task(
        #     torrent.grab_torrent_from_telegram(version=5)
        # )


def _():
    return
