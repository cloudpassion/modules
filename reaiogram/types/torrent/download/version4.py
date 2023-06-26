import gc
import re
import asyncio
import random
import time

import psutil
import tracemalloc

from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import BufferedInputFile

from config import secrets, settings
from log import logger, log_stack

from bt.encoding.stuff import from_hex_to_bytes, from_bytes_to_hex

from reaiogram.types.torrent.default import DefaultTorrent, AbstractMergedTelegram

from ..default import (
    DjangoTorrentPiece,
)

# tracemalloc.start()
# gc.disable()
UPLOAD_SEM = asyncio.Semaphore(10)


class TorrentDownloadVersion4(
    DefaultTorrent,
    AbstractMergedTelegram
):

    # pieces pack at once. size don't exceed 20MB
    async def _download_some_pieces_version4(self):

        # piece_size = self.pieces[0].length

        missing_pieces = set(self.metadata.pieces)
        # all_pieces_to_download = []
        # while self.pieces:
        for torrent_piece in self.pieces:

            dj: DjangoTorrentPiece = await torrent_piece.from_orm()

            if dj.message or dj.resume_data:
                item = [
                    p for p in missing_pieces if (
                            p.hash == from_hex_to_bytes(torrent_piece.info_hash)
                    )
                ][0]
                # index = missing_pieces.index()
                # del missing_pieces[index]
                missing_pieces.remove(item)
                # logger.info(f'piece already downloaded')
                continue

        # asyncio.create_task(
        #     self._mon_completed_and_upload_version4(
        #         missing_pieces,
        #     )
        # )
        #
        # await self.download(
        #     missing_pieces,
        #     to_bytes=True,
        # )

        asyncio.create_task(
            self.download(
                missing_pieces,
                to_bytes=True,
            )
        )
        while missing_pieces:
            try:

                await self._mon_completed_and_upload_version4(
                    missing_pieces,
                )
            except Exception as exc:
                log_stack.error('ch')
                # logger.info(f'{exc=}')
            # )
            await asyncio.sleep(1)
            logger.info(f'{missing_pieces=}')

    # def _tdt(self, h):
    #     yield self.redis.get(h)

    async def _mon_completed_and_upload_version4(
            self,
            # torrent_pieces,
            missing_pieces,
    ):

        # while True:
        #     await asyncio.sleep(10)

        piece_size = int(self.pieces[0].length)

        i = 0
        while missing_pieces:

            pieces_to_upload = []
            hashes = []
            # data = b''
            text = ''
            begin = 0
            size = 0

            while True:

                try:
                    h = self.data.pop()
                except IndexError:
                    if not missing_pieces:
                        break

                    await asyncio.sleep(1)
                    continue

                i += 1

                # pd = self.redis.get(h)

                torrent_piece = [
                    p for p in self.pieces if (
                        from_hex_to_bytes(p.info_hash) == h
                    )
                ][0]
                # logger.info(f'{piece=}, {torrent_piece=}')

                torrent_piece.begin = begin
                torrent_piece.version = 4

                pieces_to_upload.append(torrent_piece)

                text += f'{begin}|{torrent_piece.info_hash}\n'

                hashes.append(h)
                # data += self._tdt(h)
                # data += self.redis.get(h)
                begin += piece_size
                #len(pd)

                # del pd

                size += piece_size

                # self.redis.delete(h)

                # if size + piece_size >= 20971520:
                if size + piece_size >= 52428800:
                    break

            if not pieces_to_upload:
                await asyncio.sleep(1)
                continue

            tm_start = time.time()
            asyncio.create_task(
                self._mon_upload_task_version4(
                    pieces_to_upload,
                    hashes,
                    # data,
                    text,
                    missing_pieces,
                    tm_start,
                )
            )

            del pieces_to_upload
            # del data
            gc.collect()

            # if i % 10 == 0:
            #     snapshot = tracemalloc.take_snapshot()
            #     top_stats = snapshot.statistics('lineno')
            #     logger.info("[ Top 10 ]")
            #     for stat in top_stats[:10]:
            #         logger.info(f'{stat}')

    async def _mon_upload_task_version4(
            self,
            pieces_to_upload,
            hashes,
            text,
            missing_pieces,
            tm_start,
    ):

        caption = f'{self.info_hash}_{pieces_to_upload[0].info_hash}.txt'

        # data = b''
        # for h in hashes:
        #     data += self.redis.get(h)

        piece_file = BufferedInputFile(
            b''.join([self.redis.get(h) for h in hashes]),
            # data,
            filename=f'{caption}.data'
        )
        txt_file = BufferedInputFile(
            text.encode('utf8'),
            filename=f'{caption}.txt'
        )

        bt = secrets.bt.chat

        for input_file in [txt_file, piece_file, ]:
            if input_file is txt_file:
                chat_id = bt.txt.id
                thread_id = bt.txt.thread_id
            else:
                chat_id = bt.pieces.id
                thread_id = bt.pieces.thread_id

            while True:
                try:

                    async with UPLOAD_SEM:
                        message = await self.bot.send_document(
                            chat_id=chat_id,
                            message_thread_id=thread_id,
                            caption=self.info_hash,
                            document=input_file,
                        )

                    kwargs_data = await self.orm.message_to_orm(
                        message, prefix='sended'
                    )
                    break
                except TelegramRetryAfter as exc:
                    try:
                        tm = int(re.findall('Retry in (.*?) seconds', exc)[0])
                    except IndexError:
                        tm = 30
                    logger.info(f'sleep {tm=}')
                    await asyncio.sleep(tm+random.randint(1, 5))
                except Exception as exc:
                    # log_stack.error('stack upload')
                    logger.info(f'sleep 5: {exc=}')
                    await asyncio.sleep(5)

        merged_message = kwargs_data['sended_merged_message']
        for uploaded_piece in pieces_to_upload:

            uploaded_piece.message = merged_message

            await uploaded_piece._deep_to_orm()
            await uploaded_piece.update_orm()

            # x in range(0, len(pieces_to_del)+1):
            # self.data[pieces_to_del[0].hash] = None
            # del self.data[pieces_to_del[0].hash]
            # self.redis.delete(p.hash)
            try:
                self.redis.delete(uploaded_piece.piece.hash)
                missing_pieces.remove(
                    [
                        p for p in self.metadata.pieces if (
                            p.hash == uploaded_piece.piece.hash
                        )
                    ][0]
                )
            except Exception:
                logger.info(f'ch no piece: {uploaded_piece=}')
                continue

        mem_pre = psutil.Process().memory_info().rss / (1024 * 1024)
        del pieces_to_upload
        # del pieces_to_del
        # del cl_to_del

        del input_file
        del txt_file
        del piece_file
        # del data

        del message
        del merged_message

        gc.collect()
        tm_end = time.time()

        mem_after = psutil.Process().memory_info().rss / (1024 * 1024)
        # logger.info(f'uploading time: {tm_end-tm_start}')
        logger.info(f'upload complete: {tm_end-tm_start}\n'
                    f'{mem_pre=}\n{mem_after=}')
