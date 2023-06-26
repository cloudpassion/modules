import re
import asyncio
import random

from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import BufferedInputFile

from config import secrets, settings
from log import logger, log_stack

from reaiogram.types.torrent.default import DefaultTorrent, AbstractMergedTelegram

from ..default import (
    DjangoTorrentPiece,
)


class TorrentDownloadVersion1(
    DefaultTorrent,
    AbstractMergedTelegram
):

    async def _upload_completed_version1(self, piece):

        async with self.upload_sem:
            docs = []

            input_file = BufferedInputFile(
                piece.data, filename=piece.info_hash
            )
            docs.append(input_file)

            while True:
                try:
                    message = await self.bot.send_document(
                        chat_id=secrets.test.chat.id,
                        message_thread_id=secrets.test.chat.thread_id,
                        caption=piece.info_hash,
                        document=input_file,
                    )
                    break
                except TelegramRetryAfter as exc:
                    try:
                        tm = int(re.findall('Retry in (.*?) seconds', exc)[0])
                    except Exception as exc:
                        logger.info(f'time: {exc=}')
                        tm = 60

                    await asyncio.sleep(tm+random.randint(5, 10))
                except Exception:
                    log_stack.error('stack upload')
                    await asyncio.sleep(20)

            data = await self.orm.message_to_orm(message, prefix='sended')
            merged_message = data['sended_merged_message']

            piece.message = merged_message
            await piece._deep_to_orm()
            await piece.update_orm()

    async def _download_some_pieces_version1(self):

        # limit = 2
        # count = 0

        while self.pieces:
            try:
                piece = self.pieces.pop()
            except IndexError:
                break

            dj = await piece.from_orm()
            while not dj:
                dj = await piece.from_orm()
                await asyncio.sleep(1)
                logger.info(f'{dj=}')

            if dj.message:
                logger.info(f'piece already downloaded')
                continue

            if dj.resume_data:
                logger.info(f'check downloading')
                continue

            async with self.download_each_piece_sem:
                await piece.download(to_bytes=True)

            if piece.completed:
                asyncio.create_task(self._upload_completed_version1(piece))

        logger.info(f'complete download')
