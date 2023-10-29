import copy
import ctypes
import gc
import re
import asyncio
import random
import threading
import time

import psutil
# import tracemalloc

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
    async def _download_recheck_version6(self):

        dj_torrent = await self.from_orm()
        pieces = DjangoTorrentPiece.objects.filter(torrent=dj_torrent).all()

        count_pieces = len(pieces)
        logger.info(f'{dj_torrent=}, {count_pieces=} and {dj_torrent.count=}, {self.info_hash=}')

        if count_pieces != dj_torrent.count:
            logger.info(f'ret here1, {self.info_hash=}')
            return

        if not count_pieces:
            logger.info(f'ret here2, {self.info_hash=}')
            return

        br = False
        ln = 0
        for piece in pieces:

            if not piece.message:
                br = True
                ln += 1
                logger.info(f'ret here3, {piece.index=}, {piece=}, {self.info_hash=}')
                continue

            if piece.message and not piece.begin and not piece.length:
                logger.info(f'still bad begin and length: {self.info_hash=}')
                continue

        # else:
        #     return True

        if not br:
            return True

        logger.info(f'br, {ln=}, {self.info_hash=}')

    async def _download_some_pieces_version6(
            self,
            callback=None,
            tr=0,
    ):

        logger.info(f'{tr=}, {self.info_hash=}')

        tasks = []
        redis_hashes = []
        missing_pieces = set(self.metadata.pieces)

        items = {}
        logger.info(f'start creating yielding: {self.info_hash=}')
        for p in missing_pieces:
            i = p.index
            h = from_bytes_to_hex(p.hash)
            items[f'{i}_{h}'] = p

        logger.info(f'end yielding: {len(items.keys())=}, {self.info_hash=}')

        logger.info(f'{len(self.pieces)=}, {self.info_hash=}')
        try:
            p_index = 0
            for torrent_piece in self.pieces:

                p_index += 1
                # p_index = self.pieces.index(torrent_piece)
                if p_index % 1000 == 0:

                    # log = False
                    # if self.info_hash == 'aef7bed91e1af8259d5ecb112d918eb2c725ed43':
                    #     log = True

                    # if log:
                    # if True:
                    logger.info(f'{p_index=}, {self.info_hash=}')

                # await asyncio.sleep(0)
                dj: DjangoTorrentPiece = await torrent_piece.from_orm()

                info_hash = torrent_piece.info_hash
                redis = self.redis.get(f'{torrent_piece.index}_{info_hash}')
                if dj.message or dj.resume_data or redis:
                    if redis:
                        redis_hashes.append(f'{torrent_piece.index}_{info_hash}')

                    item = items[f'{torrent_piece.index}_{info_hash}']
                    # item = [
                    #     p for p in missing_pieces if (
                    #             p.hash == from_hex_to_bytes(torrent_piece.info_hash) and p.index == torrent_piece.index
                    #     )
                    # ][0]
                    # index = missing_pieces.index()
                    # del missing_pieces[index]
                    missing_pieces.remove(item)
                    # logger.info(f'piece already downloaded')
                    # continue
        except:
            log_stack.error('ch')
            return

        logger.info(f'after.ch.m: {len(missing_pieces)=}, {len(redis_hashes)=}, {self.info_hash=}')
        # if not missing_pieces:
        #     return
        #

        if redis_hashes:
            logger.info(f'start pre redis: {self.info_hash=}')
            await self._mon_completed_and_upload_version6(
                set(),
                redis_hashes
            )

            logger.info(f'pre redis complete: {self.info_hash=}')

        #mon_upload_task = asyncio.create_task(
        mon_upload = self._mon_completed_and_upload_version6(
                missing_pieces,
                [],
                set_status=True
            )
        # mon_upload_task = asyncio.ensure_future(mon_upload)
        # tasks.append(mon_upload_task)

        download = self.download(
                missing_pieces,
                to_bytes=True,
                progress_func=self.dp._pick_surge_progress
            )
        # download_task = asyncio.create_task(download)
        # tasks.append(download_task)

        upload_task = asyncio.create_task(mon_upload)
        tasks.append(upload_task)
        await download
        # asyncio.run_coroutine_threadsafe(
        #     self.download(
        #         missing_pieces,
        #         to_bytes=True,
        #         progress_func=self.dp._pick_surge_progress
        #     ),
        #     self.dp.new_loop
        # )
        # tasks.append(task)

        # await asyncio.sleep(10)

        # logger.info(f'{len(missing_pieces)=}')

        # asyncio.set_event_loop(self.dp.m_loop)

        # await self._mon_completed_and_upload_version6(
        #         missing_pieces,
        #         [],
        #         set_status=True
        # )

        logger.info(f'end1 {self.info_hash=}')
        #
        # if tasks:
        logger.info(f'start tasks: {len(tasks)=}, {self.info_hash=}')
        # if upload_tasks:
        if True:
            logger.info(f'st.upload.tasks, {upload_task=}, {self.info_hash=}')
            results = await asyncio.gather(*tasks)
            for res in results:
                logger.info(f'{res=}, {self.info_hash=}')
                await asyncio.gather(*res)

        # await mon_upload
        # await upload_task
        # await asyncio.gather(*tasks)
        logger.info(f'tasks complete: {len(tasks)=}, {self.info_hash=}')

        # logger.info(f'{callback=}')

        try:
            logger.info(f'start recheck.1, {self.info_hash=}')
            ch = await self._download_recheck_version6()
        except:
            ch = True
            log_stack.error('ch.33')

        logger.info(f'{ch=}, {self.info_hash=}')
        tr = 1
        while not ch:
            logger.info(f'start redown: {self.info_hash=}')
            await self._download_some_pieces_version6(tr=tr)
            tr += 1

            try:
                ch = await self._download_recheck_version6()
            except:
                ch = True
                log_stack.error('ch')

        while True:
            try:
                #if callback:
                    # await callback.reply(
                    #     text=f'{self.name}\n'
                    #          f'{self.info_hash}\n\n'
                    #          f'complete'
                    # )
                await self.bot.send_message(
                    chat_id=secrets.bt.chat.download.id,
                    message_thread_id=secrets.bt.chat.download.thread_id,
                    text=f'{self.name}\n'
                         f'{self.info_hash}\n\n'
                         f'complete',
                )
                break
            except (
                TelegramRetryAfter, TelegramBadRequest
            ) as exc:
                tm = self.bot.get_retry_timeout(exc)
                await asyncio.sleep(tm+random.randint(0, 5))

        logger.info(f'aft: {self.info_hash=}')

        # await self.bot.send_message(
        #     chat_id=secrets.bt.chat.download.id,
        #     text=f'{self.name}\n'
        #          f'{self.info_hash}\n\n'
        #          f'complete',
        # )

        # if set_status:
        # torrent_status = self.dp.torrents[self.info_hash]
        # torrent_status.in_work = False

        # await self.download(
        #     missing_pieces,
        #     to_bytes=True,
        #     progress_func=self.dp._pick_surge_progress
        # )
        # assert False

    async def _mon_completed_and_upload_version6(
            self,
            missing_pieces,
            redis_hashes,
            set_status=False,
    ):

        # missing_pieces = set(missing_pieces)

        logger.info(f'{self.info_hash=}:{len(missing_pieces)=}')
        logger.info(f'{len(redis_hashes)=}')
        # logger.info(f'{len(missing_pieces)}')

        # if not missing_pieces and not redis_hashes:
        #     return

        # missing_pieces = set(missing_pieces)
        tasks = []
        piece_size = max([int(x.length) for x in self.pieces])
        # logger.info(f'{piece_size=}')
        i = 0
        # dt_count = 0
        # ms_count = 0
        logger.info(f'st.gen.1 {self.info_hash=}')
        all_ms_p = {
            f'{p.index}_{from_bytes_to_hex(p.hash)}': p for p in set(missing_pieces)
        }
        logger.info(f'end.gen.1 {self.info_hash=}')
        logger.info(f'st.gen.3 {self.info_hash=}')
        all_mt_p = {
            f'{p.index}_{from_bytes_to_hex(p.hash)}': p for p in self.metadata.pieces
        }
        logger.info(f'end.gen.3 {self.info_hash=}')
        logger.info(f'st.gen.2 {self.info_hash=}')
        all_t_p = {
            f'{p.index}_{p.info_hash}': p for p in self.pieces
        }
        logger.info(f'end.gen.2 {self.info_hash=}')

        while missing_pieces or redis_hashes or self.data:

            await asyncio.sleep(1)

            pieces_to_upload = []
            hashes = []
            text = ''
            begin = 0
            size = 0

            while missing_pieces or redis_hashes or self.data:

                # await asyncio.sleep(5)
                # logger.info(f'{len(missing_pieces)=}, {len(self.data)=}\n'
                #             f'{dt_count=}\n'
                #             f'{ms_count=}')

                h = None
                if redis_hashes:
                    check_list = [redis_hashes, ]
                else:
                    check_list = [self.data, ]

                for dt in check_list:

                    if not dt:
                        continue

                    try:
                        h = dt.pop()
                        break
                    except IndexError:
                        pass
                else:
                    # logger.info(f'sleep.10 {len(missing_pieces)=}, {self.info_hash=}')
                    await asyncio.sleep(60+random.randint(30,60))
                    continue

                if not h:
                    logger.info(f'not h, {self.info_hash=}')
                    await asyncio.sleep(5)
                    continue

                _h = h
                # logger.info(f'{_h}\n\n\n\n\n\n\n\n')
                str_ind = _h.split('_')[0]
                ind = int(str_ind)
                h = _h.split('_')[1]

                i_h = f'{str_ind}_{h}'
                ms_p = all_ms_p.get(i_h)
                # ms_p = [
                #     p for p in self.metadata.pieces if (
                #             p.hash == from_hex_to_bytes(h) and p.index == ind
                #     )
                # ]
                if not ms_p:
                    # logger.info(f'not.1 {ms_p=}, {self.info_hash=}')
                    ms_p = all_mt_p[i_h]
                    if not ms_p:
                    # if True:
                        logger.info(f'not.2 {ms_p=}, {self.info_hash=}')
                        await asyncio.sleep(1)
                        continue

                try:
                    missing_pieces.remove(ms_p[0])
                except (KeyError, IndexError, TypeError) as exc:
                    # logger.info(f'not in missing {len(missing_pieces)=}, {ms_p=}, {exc=}')
                    pass

                try:
                    missing_pieces.remove(ms_p)
                except KeyError:
                    # logger.info(f'not in missing {len(missing_pieces)=}, {ms_p=}, {self.info_hash=}')
                    pass

                # ms_count += 1
                i += 1

                # pd = self.redis.get(h)

                # logger.info(f'{h=}')
                torrent_piece = all_t_p[i_h]

                # torrent_piece = [
                #     p for p in self.pieces if (
                #         p.info_hash == h and p.index == ind
                #     )
                # ][0]
                # logger.info(f'{piece=}, {torrent_piece=}')
                # logger.info(f'{torrent_piece.index=}')

                torrent_piece.begin = begin
                torrent_piece.version = 6
                # setattr(torrent_piece, 'begin', int(begin))
                # setattr(torrent_piece, 'version', 6)

                # length = len(self.redis.get(h))
                length = torrent_piece.length
                len_for_text = length if length != piece_size else ""

                text += f'{begin}|' \
                        f'{len_for_text}|' \
                        f'{torrent_piece.info_hash}\n'

                hashes.append(_h)
                begin += length
                size += length

                pieces_to_upload.append(torrent_piece)

                # 20MB
                max_file_size = 20971520
                # 50MB, TODO: very slow telethon download, event with cryptg
                # max_file_size = 52428800
                if size + length + len(f'{text}\n') + 128 >= max_file_size:
                    break

                if not missing_pieces and not self.data and not redis_hashes:
                    break

            if not pieces_to_upload:
                logger.info(f'no p to upload {self.info_hash=}, {missing_pieces=}')
                break
                # continue

            # await self._mon_upload_task_version6(
            #         pieces_to_upload,
            #         hashes,
            #         text,
            #         # missing_pieces,
            #         # tm_start,
            #     )

            # tasks variant
            # task = asyncio.create_task(
            task = asyncio.ensure_future(
               self._mon_upload_task_version6(
                   # copy.deepcopy(pieces_to_upload),
                   pieces_to_upload,
                   hashes,
                   text,
               )
            )
            tasks.append(task)
            # logger.info(f'st.upload.task')
            # await task
            # if False:
            if len(tasks) % 10 == 0: # or len(missing_pieces) <= 50:
                # if tasks:
                logger.info(f'10.0.start tasks: {len(tasks)}, {self.info_hash=}')
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f'10.0.1tasks complete: {len(tasks)}, {self.info_hash=}')
                tasks = []

            # logger.info(f'end.upload.task')
            #
            # await variant
            # await self._mon_upload_task_version6(
            #     pieces_to_upload,
            #     hashes,
            #     text,
            # )

            # del pieces_to_upload
            # del data
            # gc.collect()

            # try:
            #     if i % 20 == 0:
            #         snapshot = tracemalloc.take_snapshot()
            #         top_stats = snapshot.statistics('lineno')
            #         logger.info("[ Top 10 ]")
            #         for stat in top_stats[:10]:
            #             logger.info(f'{stat}')
            # except:
            #     log_stack.error(f'ch')

        logger.info(f'return {len(tasks)=}, {self.info_hash=}')
        return tasks
        # if tasks:
        logger.info(f'1start tasks: {self.info_hash=}')
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f'1tasks complete: {self.info_hash=}')

        # if set_status:
        #     logger.info(f'set_status: {self.info_hash=}')
        #     torrent_status = self.dp.torrents[self.info_hash]
        #     torrent_status.from_work()
        #     # torrent_status.in_work = False

    async def _mon_upload_task_version6(
            self,
            pieces_to_upload,
            hashes,
            text,
    ):
        # TODO check file name
        # i_h = [x.split("_")[1] for x in hashes]
        caption = f'{self.info_hash}_{hashes[0].split("_")[1]}'

        for h in hashes:
            if not self.redis.get(h):
                logger.info(f'mb.redown, {self.info_hash=}')
                return

        data = b''
        for h in hashes:
            data += self.redis.get(h)

        # data = b''.join([self.redis.get(h) for h in hashes])
        piece_file = BufferedInputFile(
            data,
            filename=f'{caption}.data'
        )
        setattr(piece_file, 'prefix', 'piece')

        txt_file = BufferedInputFile(
            text.encode('utf8'),
            filename=f'{caption}.txt'
        )
        setattr(txt_file, 'prefix', 'txt')

        bt = secrets.bt.chat

        kwargs_data = {}
        # for input_file in [piece_file, txt_file, ]:
        for input_file in [piece_file, ]:
            if input_file is txt_file:
                chat_id = bt.txt.id
                thread_id = bt.txt.thread_id
            else:
                chat_id = bt.pieces.id
                thread_id = bt.pieces.thread_id

            upload_bot = await self.dp.get_upload_bot()
            while True:

                await asyncio.sleep(1)

                try:
                    # async with UPLOAD_SEM and UPLOAD_AT_MINUTE and UPLOAD_AT_SECOND:
                    wu = self.dp.wait_upload
                    while wu:
                        await asyncio.sleep(wu)
                        wu = self.dp.wait_upload
                        # logger.info(f'{wu=}')

                    message = None
                    # async with self.dp.upload_sem and self.dp.upload_at_minute:
                    # async with self.dp.upload_at_minute:

                    async with self.dp.upload_at_second:
                        if True:
                    # if True:
                    # if True:
                            message = await upload_bot.send_document(
                                chat_id=chat_id,
                                message_thread_id=thread_id,
                                caption=self.info_hash,
                                document=input_file,
                            )

                    if not message:
                        raise Exception('no message')

                    kwargs_data.update(await self.orm.message_to_orm(
                        message,
                        prefix=f'{input_file.prefix}'
                    ))
                    await self.dp.put_upload_bot(upload_bot)
                    break
                except (
                        TelegramRetryAfter, TelegramBadRequest
                ) as exc:
                    tm = upload_bot.get_retry_timeout(exc)

                    self.dp.wait_upload = tm
                    logger.info(f'sleep {tm=}')
                    await asyncio.sleep(tm+random.randint(2, 10))
                    self.dp.wait_upload = 0

                except TelegramNetworkError as exc:
                    # for exc_text in (
                    #     'Request timeout error',
                    #     'no message',
                    # ):
                    #     if exc_text in f'{exc}':
                    #         continue
                    #         # upload_bot = await self.dp.new_bot(close=True)

                    upload_bot = await self.dp.new_upload_bot(
                        bot=upload_bot,
                    )
                except Exception as exc:
                    # log_stack.error('stack upload')
                    logger.info(f'sleep 30: {exc=}'[:512])
                    # self.upload_bot = self.new_bot(close=True)
                    await asyncio.sleep(30)

                    upload_bot = await self.dp.new_upload_bot(
                        bot=upload_bot,
                    )

                # logger.info(f'still upload: {self.info_hash}')

        merged_message = kwargs_data['piece_merged_message']

        async def update_piece(
                uploaded_piece,
                from_orm,
                skip=False
        ):
            # logger.info(f'{uploaded_piece._to_db_torrent=}')

            # skip_to_db for merged_message
            # at first piece merged_message is already deeped
            # at 1..len(pieces_to_upload) it raise db_hash integrity error
            # for history message update
            # because every message update run
            # history message update for save all changes
            # even no changes

            # but didn't understand why sometimes begin and version not
            # deeped into orm

            # await uploaded_piece._deep_to_orm(skip_to_db=True)
            if skip:
                await uploaded_piece._deep_to_orm(skip_to_db=['message', 'torrent', ])
            else:
                await uploaded_piece._deep_to_orm(skip_to_db=['message', ])

            while not from_orm:
                logger.info(f'wait from_orm')
                await asyncio.sleep(30)
                from_orm = await merged_message.from_orm()

            uploaded_piece._to_db_message = from_orm
            await uploaded_piece.update_orm()

            try:
                from_orm = await uploaded_piece.from_orm()
                while from_orm.message.id != merged_message.id:

                    logger.info(f'wait from_orm_id')
                    await asyncio.sleep(30)
                    from_orm = await uploaded_piece.from_orm()

                self.redis.delete(
                    f'{uploaded_piece.index}_{uploaded_piece.info_hash}'
                ) #piece.hash)
            except Exception as exc:
                logger.info(f'{exc=}')

        orm_message = await merged_message.from_orm()

        await update_piece(
            pieces_to_upload[0],
            orm_message,
            skip=False
        )

        for piece in pieces_to_upload[1:]:
            await update_piece(piece, orm_message, skip=True)

        del data
        del input_file
        del txt_file
        del piece_file
        del pieces_to_upload

        gc.collect()
        # libc = ctypes.CDLL("libc.so.6")
        # libc.malloc_trim(0)

        # end
