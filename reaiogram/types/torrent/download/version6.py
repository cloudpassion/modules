# import gc
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
UPLOAD_SEM = asyncio.Semaphore(15)


class TorrentDownloadVersion6(
    DefaultTorrent,
    AbstractMergedTelegram
):

    # pieces pack at once. size don't exceed
    # upload 50MB, but download 50MB
    # drop upload to 20MB for skip downloading by telethon
    async def _download_some_pieces_version6(
            self, twice=True
    ):

        missing_pieces = set(self.metadata.pieces)

        for torrent_piece in self.pieces:

            dj: DjangoTorrentPiece = await torrent_piece.from_orm()

            if False and dj.message or dj.resume_data:
                item = [
                    p for p in missing_pieces if (
                            p.hash == from_hex_to_bytes(torrent_piece.info_hash)
                    )
                ][0]
                # index = missing_pieces.index()
                # del missing_pieces[index]
                missing_pieces.remove(item)
                # logger.info(f'piece already downloaded')
                # continue

        if not missing_pieces:
            return

        tasks = []
        task = asyncio.create_task(
            self._mon_completed_and_upload_version6(
                missing_pieces,
            )
        )
        tasks.append(task)
        # tasks.append(task)

        # while missing_pieces:

        task = asyncio.create_task(
            self.download(
                missing_pieces,
                to_bytes=True,
            )
        )
        tasks.append(task)

        await asyncio.gather(*tasks)

        # logger.info(f'sleep 300: {twice=}')
        # await asyncio.sleep(300)
        # if twice:
        #     await self._download_some_pieces_version6(twice=False)

        # logger.info(f'{missing_pieces=}')
        # await asyncio.sleep(120)

    async def _mon_completed_and_upload_version6(
            self,
            missing_pieces,
    ):

        tasks = []
        piece_size = max([int(x.length) for x in self.pieces])
        # i = 0
        while missing_pieces:

            pieces_to_upload = []
            hashes = []
            text = ''
            begin = 0
            size = 0

            while True:

                try:
                    h = self.data.pop()
                except IndexError:
                    if not missing_pieces:
                        break

                    await asyncio.sleep(0)
                    continue

                # logger.info(f'{len(missing_pieces)=}')
                # i += 1

                # pd = self.redis.get(h)

                torrent_piece = [
                    p for p in self.pieces if (
                        from_hex_to_bytes(p.info_hash) == h
                    )
                ][0]
                # logger.info(f'{piece=}, {torrent_piece=}')

                torrent_piece.begin = begin
                torrent_piece.version = 6

                pieces_to_upload.append(torrent_piece)

                # length = len(self.redis.get(h))
                length = torrent_piece.length
                len_for_text = length if length != piece_size else ""

                text += f'{begin}|' \
                        f'{len_for_text}|' \
                        f'{torrent_piece.info_hash}\n'

                hashes.append(h)
                begin += length
                size += length

                if size + length + len(f'{text}\n') >= 20971520:
                # if size + piece_size >= 52428800:
                    await asyncio.sleep(0)
                    break

            if not pieces_to_upload:
                await asyncio.sleep(0)
                continue

            tm_start = time.time()
            task = asyncio.create_task(
                self._mon_upload_task_version6(
                    pieces_to_upload,
                    hashes,
                    text,
                    missing_pieces,
                    tm_start,
                )
            )
            tasks.append(task)

            # del pieces_to_upload
            # del data
            # gc.collect()

            # if i % 10 == 0:
            #     snapshot = tracemalloc.take_snapshot()
            #     top_stats = snapshot.statistics('lineno')
            #     logger.info("[ Top 10 ]")
            #     for stat in top_stats[:10]:
            #         logger.info(f'{stat}')

        return tasks

    async def _mon_upload_task_version6(
            self,
            pieces_to_upload,
            hashes,
            text,
            missing_pieces,
            tm_start,
    ):
        # TODO check file name
        caption = f'{self.info_hash}_{from_bytes_to_hex(hashes[0])}'

        # data = b''
        # for h in hashes:
        #     data += self.redis.get(h)

        piece_file = BufferedInputFile(
            b''.join([self.redis.get(h) for h in hashes]),
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

                    # async with UPLOAD_SEM:
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

        # # mem_pre = psutil.Process().memory_info().rss / (1024 * 1024)
        # del pieces_to_upload
        # # del pieces_to_del
        # # del cl_to_del
        #
        # del input_file
        # del txt_file
        # del piece_file
        # # del data
        #
        # del message.document
        # del merged_message.document.unmerged
        # del merged_message.document
        # del merged_message
        # del kwargs_data['sended_merged_message']

        # gc.collect()
        tm_end = time.time()

        # mem_after = psutil.Process().memory_info().rss / (1024 * 1024)
        # logger.info(f'uploading time: {tm_end-tm_start}')
        logger.info(f'upload complete: {tm_end-tm_start}\n')
                    # f'{mem_pre=}\n')
                    # f'{mem_after=}')
