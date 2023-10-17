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

        if not torrent:
            return

        torrent_status = dp.torrents[torrent.info_hash]
        if torrent_status.in_work:
            return

        torrent_status.in_work = True

        cmt = torrent.comment or torrent.publisher_url
        if not cmt:
            cmt = ''

        try:
            await self.event.reply(
                text=f'start merging\n'
                     f'{torrent.name}\n'
                     f'{cmt}\n'
                     f'{torrent.info_hash}'
            )
        except Exception as exc:
            pass

        resp = await torrent.grab_torrent_from_telegram(version=6)

        torrent_status.in_work = False

        if resp:
            await self.event.reply(
                text=f'end merging\n'
                     f'{torrent.name}\n'
                     f'{cmt}\n'
                     f'{torrent.info_hash}'
            )
        else:
            await self.event.reply(
                text=f'need redown\n'
                     f'{torrent.name}\n'
                     f'{cmt}\n'
                     f'{torrent.info_hash}'
            )

        # asyncio.create_task(
        #     torrent.grab_torrent_from_telegram(version=5)
        # )


def _():
    return
