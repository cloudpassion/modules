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

        dp.torrent[torrent.info_hash] = True
        await torrent.download_some_pieces(version=6)

        dp.torrent[torrent.info_hash] = False


def _():
    return
