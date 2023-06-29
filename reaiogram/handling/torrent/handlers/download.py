import asyncio

from aiogram import F
from aiogram.handlers import BaseHandler

from config import secrets
from log import logger

from ...torrent.router import torrent_bot_router
from ....types.torrent.torrent import TorrentFile


@torrent_bot_router.message(
    F.message_thread_id == secrets.bt.chat.download.thread_id
)
class TorrentDownloadHandler(BaseHandler):
    async def handle(self):

        dp = self.bot.dp

        data = self.data

        torrent: TorrentFile = data.get('torrent')

        if not torrent:
            return

        torrent_status = dp.torrents[torrent.info_hash]
        torrent_status.in_work = True

        asyncio.create_task(
            torrent.download_some_pieces(version=6)
        )


def _():
    return
