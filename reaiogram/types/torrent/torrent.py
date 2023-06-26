import asyncio
import random
import re
from typing import Optional

from asgiref.sync import sync_to_async, async_to_sync

from config import settings, secrets
from log import logger, log_stack

from ...default.bot import Bot
from ...django_telegram.django_telegram.datamanager.bt.piece import (
    PIECE_KEYS, PIECE_SELECT_KEYS, PIECE_HASH_KEY, PIECE_HASH_KEYS
)
from ...types.django import (
    TorrentFile as DjangoTorrentFile,
    TorrentFileHistory as DjangoTorrentFileHistory,
    TorrentPiece as DjangoTorrentPiece
)
from ..tg.merged.default.default import AbstractMergedTelegram

from bt.torrent import (
    TorrentFile as DefaultTorrentFile,
    TorrentPiece as DefaultTorrentPiece,
)

from .download.version1 import TorrentDownloadVersion1
from .download.version2 import TorrentDownloadVersion2
from .download.version3 import TorrentDownloadVersion3
from .download.version4 import TorrentDownloadVersion4
from .download.version5 import TorrentDownloadVersion5
from .download.version6 import TorrentDownloadVersion6

from .grab.version5 import TorrentGrabVersion5


class TorrentFile(
    TorrentDownloadVersion1,
    TorrentDownloadVersion2,
    TorrentDownloadVersion3,
    TorrentDownloadVersion4,
    TorrentDownloadVersion5,
    TorrentDownloadVersion6,

    TorrentGrabVersion5,
):

    async def download_torrent_from_tg(self):

        if not self.bytes_data:
            self.bytes_data = await self.bot.download(
                file=self.message.document.file_id,
            )

        self.parse()

    async def save_to_django(self):

        # await self._default_merge_telegram()
        await self._convert_to_orm()
        # self.message = await self.message.from_orm()

        await self.orm.update_one(
            data=self, db_class=DjangoTorrentFile
        )
        await self.orm.add_one_history(
            data=self, db_class=DjangoTorrentFileHistory
        )

    async def gen_pieces_from_django(self, select_all):

        hash_pieces = self.gen_pieces_data()

        for select in select_all:
            info_hash = select.info_hash
            # logger.info(f'{info_hash=}')
            # logger.info(f'{hash_pieces[info_hash]=}')

            piece = TorrentPiece(
                self.orm, self.bot, self,
                piece=hash_pieces[info_hash],
            )
            self.pieces.append(piece)

    async def add_pieces_to_django(self):

        piece = DjangoTorrentPiece()
        torrent = await self.from_orm()

        self.orm.set_select(
            data=piece,
            select_kwargs={
                'torrent': torrent,
            },
            set_keys=True
        )
        select_all = await self.orm.select_all(
            data=piece,
            db_class=DjangoTorrentPiece
        )
        # logger.info(f'{select_all=}')

        if len(select_all) == len(self.metadata.pieces):
            await self.gen_pieces_from_django(select_all)
            return

        logger.info(f'need to add pieces')
        select_hashes = [x.info_hash for x in select_all]

        logger.info(f'{len(self.metadata.pieces)=}')

        # l = 0
        for metadata_piece in self.metadata.pieces:
            # l += 1
            # logger.info(f'{metadata_piece=}')
            piece = TorrentPiece(
                self.orm, self.bot, torrent=self,
                piece=metadata_piece,
            )

            if piece.info_hash in select_hashes:
                # logger.info(f'continue')
                continue

            await piece._deep_to_orm()

            self.pieces.append(piece)

            # if l >= 10:
            #     break

        # logger.info(f'{self.pieces=}')
        await self.bulk_pieces_to_orm()

    async def grab_torrent_from_telegram(
            self,
            version
    ):
        if not self.pieces:
            logger.info(f'all pieces already downloaded')
            return

        root_dir = '/exm/wd1000blk/temp_tg'
        out_dir = f'{root_dir}/out'

        if 5 <= version <= 6:
            await self.grab_torrent_from_telegram_version5(
                out_dir=out_dir,
                version=version
            )

    async def download_some_pieces(
            self,
            version
    ):

        logger.info(F'download some pieces')

        if not self.pieces:
            logger.info(f'all pieces already downloaded')
            return

        # each piece in one message
        if version == 1:
            async with self.download_sem:
                await self._download_some_pieces_version1()

        # piece+piece+piece in one file less than 20MB
        if version == 2:
            async with self.download_sem:
                await self._download_some_pieces_version2()

        if version == 3:
            await self._download_some_pieces_version3()

        if version == 4:
            await self._download_some_pieces_version4()

        if version == 5:
            await self._download_some_pieces_version5()

        if version == 6:
            await self._download_some_pieces_version6()

        logger.info(f'dwn complete: {version=}')
        try:
            del self.dp.torrent[self.info_hash]
        except KeyError:
            pass

    async def bulk_pieces_to_orm(self):
        return await self.orm.bulk_add(
            data=self.pieces, db_class=DjangoTorrentPiece

        )

    async def to_orm(self):
        return await self.orm.update_one(
            data=self, db_class=DjangoTorrentFile
        )

    async def from_orm(self):
        return await self.orm.select_one(
            data=self, db_class=DjangoTorrentFile
        )


class TorrentPiece(
    DefaultTorrentPiece,
    AbstractMergedTelegram,
):

    unmerged: Optional = None
    hash_key = PIECE_HASH_KEY
    db_keys = PIECE_KEYS
    select_keys = PIECE_SELECT_KEYS

    def __init__(
            self, orm, bot, torrent: TorrentFile,
            piece,
    ):
        self.db_class = DjangoTorrentPiece
        self.orm = orm
        self.bot: Bot = bot

        self.orm.hash_strings[self.hash_key] = PIECE_HASH_KEYS
        self.torrent = torrent

        super(DefaultTorrentPiece, self).__init__(
            piece=piece,
            metadata=torrent.metadata,
            peer_id=torrent.peer_id,
        )

    # async def download_file(self):
    #
    #     if self.bytes_data:
    #         return
    #
    #     self.bytes_data = await self.bot.download(
    #         file=self.message.document.file_id,
    #     )

    async def save_to_django(self):

        await self._convert_to_orm()

        await self.orm.update_one(
            data=self, db_class=DjangoTorrentFile
        )
        await self.orm.add_one_history(
            data=self, db_class=DjangoTorrentFileHistory
        )

    async def update_orm(self):
        return await self.orm.update_one(
            data=self, db_class=DjangoTorrentPiece
        )

    async def to_orm(self):
        return await self.orm.add_one(
            data=self, db_class=DjangoTorrentPiece
        )

    async def from_orm(self):

        torrent = await self.torrent.from_orm()
        self.orm.set_select(
            data=self,
            select_kwargs={
                'torrent': torrent,
                'info_hash': self.info_hash,
            }
        )

        return await self.orm.select_one(
            data=self, db_class=DjangoTorrentPiece
        )
