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


class TorrentDownloadVersion2(
    DefaultTorrent,
    AbstractMergedTelegram
):

    async def _download_some_pieces_version2(self):

        piece_size = self.pieces[0].length

        while self.pieces:

            piece_to_upload = []
            size = 0
            while size + piece_size < 20971520:

                try:
                    piece = self.pieces.pop()
                except IndexError:
                    break

                dj: DjangoTorrentPiece = await piece.from_orm()

                if dj.message:
                    logger.info(f'piece already downloaded')
                    continue

                if dj.resume_data:
                    logger.info(f'check downloading')
                    continue

                async with self.download_each_piece_sem:
                    await piece.download(to_bytes=True)

                    if piece.completed:
                        piece_to_upload.append(piece)

                        size += piece.length

                        # logger.info(f'{(size*1024*1024)=}')

            asyncio.create_task(
                self._upload_completed_version2(piece_to_upload.copy())
            )

        logger.info(f'end download')

    async def _upload_completed_version2(
            self, pieces
    ):

        if not pieces:
            logger.info(f'no pieces to upload')
            return

        async with self.upload_sem:
            data = b''
            text = ''
            begin = 0
            for piece in pieces:

                piece.version = 2
                piece.begin = begin

                text += f'{begin}|{piece.info_hash}\n'
                data += piece.data
                begin += len(piece.data)

            caption = f'{self.info_hash}_{pieces[0].info_hash}.txt'
            piece_file = BufferedInputFile(
                data, filename=f'{caption}.data'
            )
            txt_file = BufferedInputFile(
                text.encode('utf8'), filename=f'{caption}.txt'
            )

            for input_file in (txt_file, piece_file):
                while True:
                    try:
                        bt = secrets.bt.chat
                        if input_file is txt_file:
                            chat_id = bt.txt.id
                            thread_id = bt.txt.thread_id
                        else:
                            chat_id = bt.pieces.id
                            thread_id = bt.pieces.thread_id

                        message = await self.bot.send_document(
                            chat_id=chat_id,
                            message_thread_id=thread_id,
                            caption=self.info_hash,
                            document=input_file,
                        )

                        # await self.orm.message_to_orm(message, prefix='sended')
                        data = await self.orm.message_to_orm(message, prefix='sended')
                        break
                    except TelegramRetryAfter as exc:
                        try:
                            tm = int(re.findall('Retry in (.*?) seconds', exc)[0])
                        except Exception:
                            tm = 60
                        logger.info(f'sleep {tm=}')
                        await asyncio.sleep(tm+random.randint(1, 5))
                    except Exception:
                        # log_stack.error('stack upload')
                        logger.info(f'sleep 20')
                        await asyncio.sleep(20)

            merged_message = data['sended_merged_message']
            for piece in pieces:

                piece.message = merged_message
                await piece._deep_to_orm()
                await piece.update_orm()
