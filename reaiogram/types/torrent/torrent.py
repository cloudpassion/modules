from typing import Optional

from asgiref.sync import sync_to_async, async_to_sync

from log import logger

from ...default.bot import Bot
from ...django_telegram.django_telegram.datamanager.bt.torrent import (
    TORRENT_KEYS, TORRENT_SELECT_KEYS, TORRENT_HASH_KEY
)
from ...types.django import (
    TorrentFile as DjangoTorrentFile,
    TorrentFileHistory as DjangoTorrentFileHistory,
)
from ..tg.merged.default.default import AbstractMergedTelegram

from bt.torrent import TorrentFile as DefaultTorrentFile


class TorrentFile(
    DefaultTorrentFile,
    AbstractMergedTelegram,
):

    unmerged: Optional = None
    hash_key = TORRENT_HASH_KEY
    db_keys = TORRENT_KEYS
    select_keys = TORRENT_SELECT_KEYS

    def __init__(
            self, orm, bot, merged_message
    ):
        self.db_class = DjangoTorrentFile
        self.orm = orm
        self.bot: Bot = bot

        self.orm.hash_strings[self.hash_key] = self.db_keys

        self.message = merged_message
        self.info = merged_message.text or merged_message.caption

    async def download_file(self):

        if self.bytes_data:
            return

        self.bytes_data = await self.bot.download(
            file=self.message.document.file_id,
        )

    async def save_to_django(self):

        self.parse_torrent()

        # await self._default_merge_telegram()
        await self._convert_to_orm()
        # self.message = await self.message.from_orm()

        await self.orm.update_one(
            data=self, db_class=DjangoTorrentFile
        )
        await self.orm.add_one_history(
            data=self, db_class=DjangoTorrentFileHistory
        )

    async def to_orm(self):
        return await self.orm.update_one(
            data=self, db_class=DjangoTorrentFile
        )

    async def from_orm(self):
        return await self.orm.select_one(
            data=self, db_class=DjangoTorrentFile
        )
