import asyncio

from aiogram import F
from aiogram.types import BufferedInputFile
from aiogram.handlers import BaseHandler
from aiogram.types import Message

from config import secrets
from log import logger

from ...torrent.router import torrent_bot_router
from ....types.torrent.torrent import TorrentFile
from bt.encoding.stuff import from_hex_to_bytes
from bt.dht.torrent import DHTMakeTorrent


@torrent_bot_router.message(
    F.message_thread_id == secrets.bt.chat.magnet.thread_id
)
class TorrentMagnetHandler(BaseHandler):
    async def handle(self):

        bot = self.bot
        dp = self.bot.dp
        data = self.data
        event: Message = self.event

        if not event.text and not event.caption:
            return

        text = self.event.text or self.event.caption

        # if len(text) != 40:
        #     return
        #
        # try:
        #     from_hex_to_bytes(text)
        # except Exception as exc:
        #     logger.info(f'{exc=}')
        #     return

        info_hash, magnet = None, None

        if len(text) == 40:
            info_hash = text
        else:
            magnet = text

        cl = DHTMakeTorrent()
        torrent_data = await cl.get_from_http(magnet=magnet, info_hash=info_hash)

        if not torrent_data:
            return

        merged_message = data['merged_message'] or data['edtited_merged_message']
        torrent = TorrentFile(
            orm=dp.orm,
            bot=bot,
            dp=dp,
            merged_message=merged_message,
        )

        torrent.bytes_data = torrent_data
        torrent.parse()

        doc = BufferedInputFile(
            torrent_data,
            filename=f'{torrent.name}.torrent'
        )

        await bot.send_document(
            chat_id=event.chat.id,
            document=doc,
            reply_to_message_id=event.message_id,
            caption='test'
        )
        #
        # torrent_status = dp.torrents[torrent.info_hash]
        # torrent_status.in_work = True
        #
        # if not torrent:
        #     return
        #
        # await torrent.grab_torrent_from_telegram(version=6)
        #
        # torrent_status.in_work = False
        #
        # # asyncio.create_task(
        # #     torrent.grab_torrent_from_telegram(version=5)
        # # )


def _():
    return
