import os
import time
import asyncio
import functools
import random

from aiolimiter import AsyncLimiter

from surge.metadata import (
    valid_piece_data,
    # make_chunks,
    # Chunk
)

from config import secrets
from log import logger, log_stack

from ..default import DefaultTorrent
from ....encoding.stuff import from_bytes_to_hex
from ...stuff.check import redis_memory_wait
from .resurge import (
    make_chunks,
    Chunk
)

LIMITER = {
    # 'main': asyncio.Semaphore(15),
    'main': asyncio.Semaphore(1),
}


async def chunk_task(
        n, chunk: Chunk, folder, loop, limiter, redis, info_hash, piece
):

    #if True:
    async with limiter[folder]:
        await redis_memory_wait(
            r=redis,
            more_total=piece.length*50,
            info=f'put, {info_hash}',
        )
    # async with limiter[folder]:
    # if True:
        # chunk: Chunk
        try:
            # ch = chunk.read(folder)
            ch = await chunk.aio_read(folder)

            # ch = await loop.run_in_executor(
            #     None, functools.partial(
            #         chunk.read,
            #         folder
            #     )
            # )

            # try:
            #     logger.info(f'{len(ch)}, {len(dt)}')
            #     logger.info(f'{ch=}'[:12])
            #     logger.info(f'{dt=}'[:12])
            # except Exception as exc:
            #     logger.info(f'{exc=}')
            # data.append(ch)

            return n, ch
        except FileNotFoundError as exc:
            logger.info(f'{exc=}')
            return
        except Exception as exc:
            log_stack.error('ch')
            return


async def piece_check_task(
        piece, m_pieces, folder,
        chunks, redis, max_memory,
        torrent, info_hash, null_data,
        limiter, loop
):

    # limiter = LIMITER

    if True:
        # if True:
        # try:
        # if True:

        # async with limiter[folder]:
        if True:
            # logger.info(3)
            # logger.info(f'{limiter.get(info_hash)=}')
            if True:
            # async with limiter[folder]:
            # async with limiter[info_hash]:
                # async with limiter[f'{folder}_{from_bytes_to_hex(piece.hash)}']:
    #         async with limiter[info_hash]:
    #         if True:
                if True:
                # logger.info(4)
                # if True:
                # async with limiter['main']:
                #     logger.info(5)
                    # logger.info(f'h: {self.info_hash}, check: {piece=}')
                    # loop = asyncio.get_running_loop()

                    chunk_pieces = chunks[piece]
                    data = [None for x in chunk_pieces]
                    # chunk_tasks = []
                    # for _n, _chunk in enumerate(chunks[piece]):
                    #
                    #     _task = asyncio.ensure_future(
                    #     # _task = asyncio.create_task(
                    #         chunk_task(_n, _chunk, folder)
                    #     )
                    #     chunk_tasks.append(_task)
                    #
                    # # logger.info(f'{len(chunk_tasks)=}')
                    # # logger.info(f'{len(data)=}')
                    # results = await asyncio.gather(*chunk_tasks, return_exceptions=False)
                    # # logger.info(f'{len(results)=}')
                    results = []
                    for _n, _chunk in enumerate(chunk_pieces):

                        if True:
                        # async with limiter[folder]:
                        #     await redis_memory_wait(
                        #         r=redis,
                        #         more_total=piece.length*50,
                        #         info=f'put, {info_hash}',
                        #     )
                            res = await chunk_task(
                                _n, _chunk, folder, loop, limiter,
                                redis, info_hash, piece
                            )
                            results.append(res)

                    # logger.info(f'{len(results)=}, {info_hash=}')

                    while True:
                        try:
                            pop = results.pop()
                        except IndexError:
                            break

                        if not pop:
                            return

                        x, _ch = pop
                        if _ch is None:
                        # if not _ch:
                            logger.info(f'h4, {x=}, {pop=}')
                            return

                        # try:
                        #     if len(_ch) == 0:
                        #         logger.info(f'{len(_ch)=}, {piece.index=}, {from_bytes_to_hex(torrent.info_hash)=}')
                        #         return
                        # except Exception:
                        #     log_stack.error(f'{piece.index=}, {from_bytes_to_hex(torrent.info_hash)=}')
                        #     return

                        data[x] = _ch

                    bytes_data = b"".join(data)
                    if valid_piece_data(piece, bytes_data):

                        # logger.info(f'put: {piece}, {self.info_hash}')
                        # asyncio.run(
                        #     torrent.put_piece(
                        #         peer=None, piece=piece, data=bytes_data
                        #     )
                        # )
                        # logger.info(f'put')
                        await torrent.put_piece(
                            peer=None, piece=piece, data=bytes_data
                        )
                    else:
                        if bytes_data != null_data:
                            logger.info(f'{len(bytes_data)=}, {len(null_data)=}')
                            logger.info(f'data not valid: {info_hash=}, {piece.index=}\n'
                                        f'{len(bytes_data)=}, '
                                        f'{piece.length=}\n'
                                        f'{len(null_data)}\n'
                                        f'{data=}'[:512])
        # except:
        #     log_stack.error('df')


class TorrentDefaultDownload(
    DefaultTorrent
):

    @staticmethod
    def valid_piece_data(piece, data):
        return valid_piece_data(piece, data)

    # async def _check_dwn_in_files_loop(
    async def _check_dwn_in_files_loop(
            self, folder, torrent, chunks, m_pieces, limiter, info_hash, loop
    ):

        # try:

        if True:
            if not m_pieces:
                logger.info(f'not. {m_pieces=}, {info_hash=}')
                return

            max_memory = 1
            #int(self.redis.config_get('maxmemory')['maxmemory'])

            try:
                null_data = b''.join([b'\x00' for _ in range(0, list(m_pieces)[0].length)])
            except (IndexError, ):
                null_data = b'\x00'

            tasks = []
            for _piece in set(m_pieces):
                # task = asyncio.ensure_future(
                # task = asyncio.create_task(
                #     piece_check_task(_piece)
                # )

                if _piece not in m_pieces:
                    continue

                # await piece_check_task(
                #     piece=_piece, m_pieces=m_pieces,
                #     folder=folder, chunks=chunks,
                #     redis=self.redis, max_memory=max_memory,
                #     torrent=torrent
                # )

                task = asyncio.ensure_future(
                # task = asyncio.create_task(
                    piece_check_task(
                        piece=_piece, m_pieces=m_pieces,
                        folder=folder, chunks=chunks,
                        redis=self.redis, max_memory=max_memory,
                        torrent=torrent,
                        info_hash=info_hash,
                        null_data=null_data,
                        limiter=limiter,
                        loop=loop,
                    )
                )

                tasks.append(task)

                # logger.info(1)
                # try:
                #     await piece_check_task(
                #             piece=_piece, m_pieces=m_pieces,
                #             folder=folder, chunks=chunks,
                #             redis=self.redis, max_memory=max_memory,
                #             torrent=torrent,
                #             info_hash=info_hash,
                #             null_data=null_data,
                #             limiter=limiter
                #     )
                # except:
                #     log_stack.error('asdf')
                # logger.info(2)

            return tasks
            # await asyncio.gather(*tasks)
        # except:
        #     log_stack.error('asdfasdfa')

    async def dwn_tree_check(
            self, torrent, missing_pieces, info_hash, ident
    ):

        # try:
        if True:
            try:
                folders = secrets.bt.nas_folders
            except AttributeError:
                logger.info('no folder in config')
                return

            chunks = make_chunks(self.metadata.pieces, self.metadata.files)
            limiter = LIMITER
            if not limiter.get(info_hash):
                logger.info(f'create limiter for {info_hash=}')
                limiter[info_hash] = AsyncLimiter(
                    1,
                    # time_period=3600.0+float(
                    #     random.randint(1200, 2400)
                    # )
                    time_period=900.0+float(
                        random.randint(300, 600)
                    )
                )
            # limiter = {
            #     'main': asyncio.Semaphore(20)
            # }

            loop = asyncio.get_running_loop()
            while missing_pieces:

                await asyncio.sleep(0)
                folder_tasks = []
                for folder in folders:

                    await asyncio.sleep(0)

                    if not os.path.isdir(os.path.realpath(folder)):
                        # logger.info(f'nas {folder=} dont exist')
                        continue

                    path = f'{folder}/{self.name}'
                    realpath = os.path.realpath(path)
                    if not os.path.isfile(realpath) and not os.path.isdir(realpath):
                        # logger.info(f'torrent dont exist in {path=}')
                        continue

                    if not limiter.get(folder):
                        limiter[folder] = asyncio.Semaphore(3)

                    # for _piece in set(missing_pieces):
                    #     k = f'{folder}_{from_bytes_to_hex(_piece.hash)}'
                    #     if limiter.get(k):
                    #         continue
                    #
                    #     limiter[k] = AsyncLimiter(
                    #         1,
                    #         time_period=600.0+float(
                    #             random.randint(600, 900)
                    #         )
                    #     )
                    #
                    # loop = asyncio.get_running_loop()
                    # await loop.run_in_executor(
                    #     None, functools.partial(
                    #         self._check_dwn_in_files_loop,
                    #         folder, torrent, chunks, missing_pieces
                    #     )
                    # )

                    # folder_task = asyncio.create_task(
                    #     self._check_dwn_in_files_loop(
                    #         folder, torrent, chunks, missing_pieces, limiter
                    #     )
                    # )
                    # folder_tasks.append(folder_task)

                    folder_task = await self._check_dwn_in_files_loop(
                        folder, torrent, chunks, missing_pieces, limiter, info_hash, loop
                    )

                    if not folder_task:
                        continue

                    folder_tasks.extend(folder_task)

                if not folder_tasks:
                    logger.info(f'no tasks, {info_hash=}')
                    await asyncio.sleep(60)
                    continue

                # split = 10
                logger.info(f'{ident}.gather 1, {info_hash=}, {len(folder_tasks)=}')
                # while folder_tasks:
                #
                #     split_tasks = []
                #     for _ in range(0, split+1):
                #         try:
                #             t = folder_tasks.pop()
                #         except IndexError:
                #             break
                #
                #         split_tasks.append(t)
                #
                #     logger.info(f'st_task')
                #     await asyncio.gather(*split_tasks)

                # async with limiter[info_hash]:
                # async with limiter[folder]:
                random.shuffle(folder_tasks)
                # logger.info(f'gather 2.1, {self.info_hash=}, {len(folder_tasks)=}')
                if True:
                    async with limiter[info_hash]:
                        logger.info(f'{ident}.gather 2.2, {info_hash=}, {len(folder_tasks)=}')
                        results = await asyncio.gather(*folder_tasks, return_exceptions=True)
                        for res in results:
                            if res:
                                logger.info(f'{res=}, {self.info_hash=}')

                        logger.info(f'{ident}.gather end.1, {info_hash=}, {len(folder_tasks)=}')

                logger.info(f'{ident}.gather end.2, {info_hash=}, {len(folder_tasks)=}')
                # await asyncio.sleep(600+random.randint(300, 600))
        # except:
        #     log_stack.error('asdfasdf')
