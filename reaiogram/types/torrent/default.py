import asyncio

from typing import Optional

from config import settings, secrets

from ...default.bot import Bot
from ...types.django import (
    TorrentFile as DjangoTorrentFile,
    TorrentFileHistory as DjangoTorrentFileHistory,
    TorrentPiece as DjangoTorrentPiece
)
from reaiogram.types.tg.merged.default.default import AbstractMergedTelegram
from ...django_telegram.django_telegram.datamanager.bt.torrent import (
    TORRENT_KEYS, TORRENT_SELECT_KEYS, TORRENT_HASH_KEY
)
from bt.torrent import (
    TorrentFile as DefaultTorrentFile,
    TorrentPiece as DefaultTorrentPiece,
)


class DefaultTorrent(
    DefaultTorrentFile,
    AbstractMergedTelegram,
):

    unmerged: Optional = None
    hash_key = TORRENT_HASH_KEY
    db_keys = TORRENT_KEYS
    select_keys = TORRENT_SELECT_KEYS

    def __init__(
            self, orm, bot, merged_message, dp
    ):
        self.db_class = DjangoTorrentFile
        self.orm = orm
        self.bot: Bot = bot

        self.orm.hash_strings[self.hash_key] = self.db_keys

        self.message = merged_message
        self.info = merged_message.text or merged_message.caption

        self.download_sem = asyncio.Semaphore(2)
        self.download_each_piece_sem = asyncio.Semaphore(10)
        self.upload_sem = asyncio.Semaphore(1)

        self.dp = dp
        super(DefaultTorrentFile, self).__init__()
