# import gc
import re
import asyncio
import random
import time

import psutil
import tracemalloc

from aiolimiter import AsyncLimiter
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramBadRequest,
    TelegramNetworkError,
)
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
# UPLOAD_SEM = asyncio.Semaphore(10)
# UPLOAD_AT_MINUTE = AsyncLimiter(29)
# UPLOAD_AT_SECOND = AsyncLimiter(1, time_period=1)


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

        redis_hashes = []
        missing_pieces = set(self.metadata.pieces)

        for torrent_piece in self.pieces:

            # continue

            dj: DjangoTorrentPiece = await torrent_piece.from_orm()

            info_hash = torrent_piece.info_hash
            redis = self.redis.get(info_hash)
            if dj.message or dj.resume_data or redis:
                if redis:
                    redis_hashes.append(info_hash)

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

            await asyncio.sleep(0)

        # if not missing_pieces:
        #     return
        #
        tasks = []
        task = asyncio.create_task(
            self._mon_completed_and_upload_version6(
                missing_pieces,
                redis_hashes,
            )
        )
        tasks.append(task)

        # while missing_pieces:

        # task = asyncio.create_task(
        await self.download(
                missing_pieces,
                to_bytes=True,
            )

        # await asyncio.gather(*tasks)

    async def _mon_completed_and_upload_version6(
            self,
            missing_pieces,
            redis_hashes,
    ):

        logger.info(f'{len(missing_pieces)=}')
        logger.info(f'{len(redis_hashes)=}')
        # logger.info(f'{len(missing_pieces)}')

        # missing_pieces = set(missing_pieces)
        tasks = []
        piece_size = max([int(x.length) for x in self.pieces])
        # i = 0
        # dt_count = 0
        # ms_count = 0
        while missing_pieces or redis_hashes:

            await asyncio.sleep(1)

            pieces_to_upload = []
            hashes = []
            text = ''
            begin = 0
            size = 0

            while missing_pieces or redis_hashes:

                await asyncio.sleep(1)
                # logger.info(f'{len(missing_pieces)=}, {len(self.data)=}\n'
                #             f'{dt_count=}\n'
                #             f'{ms_count=}')

                for dt in [self.data, redis_hashes]:

                    try:
                        h = dt.pop()
                        break
                    except IndexError:
                        await asyncio.sleep(1)
                        continue
                else:
                    await asyncio.sleep(30)
                    continue

                ms_p = [
                    p for p in self.metadata.pieces if (
                            p.hash == from_hex_to_bytes(h)
                    )
                ]
                # logger.info(f'{ms_p=}')
                try:
                    missing_pieces.remove(ms_p[0])
                except KeyError:
                    pass

                # ms_count += 1
                # i += 1

                # pd = self.redis.get(h)

                # logger.info(f'{h=}')
                torrent_piece = [
                    p for p in self.pieces if (
                        p.info_hash == h
                    )
                ][0]
                # logger.info(f'{piece=}, {torrent_piece=}')

                torrent_piece.begin = begin
                torrent_piece.version = 6

                # length = len(self.redis.get(h))
                length = torrent_piece.length
                len_for_text = length if length != piece_size else ""

                text += f'{begin}|' \
                        f'{len_for_text}|' \
                        f'{torrent_piece.info_hash}\n'

                hashes.append(h)
                begin += length
                size += length

                pieces_to_upload.append(torrent_piece)

                if size + length + len(f'{text}\n') >= 20971520:
                # if size + piece_size >= 52428800:
                    break

                if not missing_pieces and not self.data and not redis_hashes:
                    break

            if not pieces_to_upload:
                continue

            # tm_start = time.time()
            # task = \
            task = asyncio.create_task(
                self._mon_upload_task_version6(
                    pieces_to_upload,
                    hashes,
                    text,
                    # missing_pieces,
                    # tm_start,
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

        # await asyncio.gather(*tasks)
        # return tasks

    async def _mon_upload_task_version6(
            self,
            pieces_to_upload,
            hashes,
            text,
            # missing_pieces,
            # tm_start,
    ):
        # TODO check file name
        caption = f'{self.info_hash}_{hashes[0]}'

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

            upload_bot = await self.dp.get_upload_bot()
            while True:
                try:

                    # async with UPLOAD_SEM and UPLOAD_AT_MINUTE and UPLOAD_AT_SECOND:
                    async with (
                            self.dp.upload_sem
                        ) and (
                            self.dp.upload_at_minute
                        ) and (
                            self.dp.upload_at_second
                    ):
                        message = await upload_bot.send_document(
                            chat_id=chat_id,
                            message_thread_id=thread_id,
                            caption=self.info_hash,
                            document=input_file,
                        )
                        if not message:
                            raise Exception('no message')

                    kwargs_data = await self.orm.message_to_orm(
                        message, prefix='sended'
                    )
                    await self.dp.put_upload_bot(upload_bot)
                    break
                except (
                        TelegramRetryAfter, TelegramBadRequest
                ) as exc:
                    try:
                        tm = int(re.findall('Retry in (.*?) seconds', f'{exc}')[0])
                    except Exception:
                        tm = 50
                    # logger.info(f'sleep {tm=}')
                    await asyncio.sleep(tm+random.randint(10, 20))
                except TelegramNetworkError as exc:
                    for exc_text in (
                        'HTTP Client says - Request timeout error',
                        'no message',
                    ):
                        if exc_text in f'{exc}':
                            continue
                            # upload_bot = await self.dp.new_bot(close=True)

                    upload_bot = await self.dp.new_upload_bot(
                        bot=upload_bot,
                    )
                except Exception as exc:
                    # log_stack.error('stack upload')
                    logger.info(f'sleep 5: {exc=}')
                    # self.upload_bot = self.new_bot(close=True)
                    await asyncio.sleep(30)

                await asyncio.sleep(0)

        merged_message = kwargs_data['sended_merged_message']
        for uploaded_piece in pieces_to_upload:

            # logger.info(f'{uploaded_piece._to_db_torrent=}')

            await uploaded_piece._deep_to_orm()
            uploaded_piece._to_db_message = await merged_message.from_orm()
            await uploaded_piece.update_orm()

            self.redis.delete(uploaded_piece.info_hash) #piece.hash)

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
        # tm_end = time.time()

        # mem_after = psutil.Process().memory_info().rss / (1024 * 1024)
        # logger.info(f'uploading time: {tm_end-tm_start}')
        logger.info(f'upload complete') #: {tm_end-tm_start}\n')
                    # f'{mem_pre=}\n')
                    # f'{mem_after=}')
