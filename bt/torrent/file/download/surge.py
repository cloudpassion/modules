import gc
import os
import string
import random
import asyncio
import binascii

from surge.protocol import (
    # Torrent as SurgeTorrent,
    Channel,
    #print_progress,
    # download_from_peer_loop,
)

from bt.tracker.resurge import Trackers

from log import logger, log_stack

from .default import TorrentDefaultDownload
from .resurge import (
    download_from_peer_loop,
    Torrent,
    Peer,
)
from ....encoding.stuff import from_bytes_to_hex

from .progress.console import print_progress


class PD:

    def __init__(self, piece, data):
        self.piece = piece
        self.data = data


async def collect_result(
        piece, data, sl, to_bytes
):

    # logger.info(f'ins.cl')

    if sl.valid_piece_data(piece, data):
        if to_bytes:
            hex_hash = from_bytes_to_hex(piece.hash)
            i_h = f'{piece.index}_{hex_hash}'

            # g = self.redis.get(i_h)
            # if not g:
            # while g:
            #     logger.info(f'wait until same piece uploading')
            #     await asyncio.sleep(10)
            #     g = self.redis.get(i_h)

            # logger.info(f'ins.1')
            while True:

                # logger.info(f'ins.2')
                try:
                    sl.redis.set(i_h, data)
                except Exception as exc:
                    logger.info(f'rd: {exc=}')
                    await asyncio.sleep(120)
                    continue

                g = sl.redis.get(i_h)
                if g:
                    break

                logger.info(f'wait for re, set variable for {i_h=}')
                await asyncio.sleep(10)

            sl.data.append(i_h)

    else:
        logger.info(f'no valid: {piece.index=}')

    # logger.info(f'ins.4')
    del piece

    del data

    gc.collect()


async def temp_sleep():

    while True:
        # logger.info(f'sl')
        await asyncio.sleep(1)
        # logger.info(f'sl.2')

    # await asyncio.sleep(0)


class test_with:

    def __init__(self):
        self._tasks = []

    async def __aenter__(self):
        self._tasks = [asyncio.create_task(temp_sleep()), ]
        return self

    async def __aexit__(self, *args, **kwargs):

        t_tasks = self._tasks
        for t_task in t_tasks:

            t_task.cancel()


class TorrentSurgeDownload(
    TorrentDefaultDownload
):

    async def _surge_download(
            self,
            missing_pieces,
            to_bytes,
            to_file=None,
            max_peers=100,
            max_requests=5,
            progress_func=print_progress,
    ):

        max_peers = 15
        """Download the files represented by `metadata` to piece.data attribute."""
        peer_id = self.peer_id

        metadata = self.metadata
        info_hash = metadata.info_hash
        # metadata.pieces = pieces

        tasks = set()
        gather_tasks = set()

        try:
            async with Trackers(
                    info_hash, peer_id.encode('utf8'), metadata.announce_list, max_peers
            ) as trackers:

                results = Channel(max_peers)
                pieces = metadata.pieces
                torrent = Torrent(pieces, missing_pieces, results)

                # try:
                #     await self.dwn_tree_check(
                #         torrent, missing_pieces,
                #     )
                # except Exception as exc:
                #     log_stack.error('ch')

                ident = random.randint(1,10000)
                try:

                    if missing_pieces:
                    # if True:

                        task = asyncio.create_task(
                            self.dwn_tree_check(torrent, missing_pieces, self.info_hash, ident)
                        )
                        gather_tasks.add(task)

                        for ip_ports in self.extra_peers:
                            ip, ports = ip_ports
                            for port in ports:
                                peer = Peer.from_string(f'{ip}:{port}')
                                # logger.info(f'{peer=}')

                                # rnd = ''.join(random.choices(string.ascii_lowercase, k=2))
                                # rnd2 = ''.join(random.choices(string.ascii_uppercase, k=4))
                                # peer_id = f'-qB4450-{rnd}Nm{rnd2}PXWj'
                                rnd = ''.join(random.choices(string.digits, k=2))
                                peer_id = f'-qB44{rnd}-spNmDQXWPXWj'

                                tasks.add(
                                    asyncio.create_task(
                                        download_from_peer_loop(
                                            torrent, trackers,
                                            info_hash,
                                            peer_id.encode('utf8'),
                                            pieces, max_requests*1000,
                                            self.redis, peer,
                                            force_reconnect=True,
                                            # missing_pieces,
                                        )
                                    )
                                )

                        # for _ in range(max_peers):
                        #
                        #     # rnd = ''.join(random.choices(string.ascii_lowercase, k=2))
                        #     # rnd2 = ''.join(random.choices(string.ascii_uppercase, k=4))
                        #     # peer_id = f'-qB4450-{rnd}Nm{rnd2}PXWj'
                        #     # rnd = ''.join(random.choices(string.digits, k=2))
                        #     # peer_id = f'-qB44{rnd}-spNmDQXWPXWj'
                        #     tasks.add(
                        #         asyncio.create_task(
                        #             download_from_peer_loop(
                        #                 torrent, trackers,
                        #                 info_hash,
                        #                 peer_id.encode('utf8'),
                        #                 pieces, max_requests,
                        #                 self.redis,
                        #                 # missing_pieces=missing_pieces,
                        #             )
                        #         )
                        #     )
                        # tasks.add(
                        asyncio.create_task(
                            progress_func(
                                torrent,
                                trackers,
                                self.info_hash
                            )
                        )
                        # )
                    async for piece, data in results:
                        await collect_result(piece, data, self, to_bytes)

                    logger.info(f'here0: {self.info_hash=}')
                except Exception:
                    log_stack.error('1')
                finally:

                    logger.info(f'here1.1: {self.info_hash=}')
                    for _url, task in trackers._trackers.items():
                        logger.info(f'{_url}, {task=}')
                        try:
                            task.cancel()
                        except Exception as exc:
                            logger.info(f'{exc[:512]}')

                    logger.info(f'here: {self.info_hash=}')
                    for task in tasks:
                        try:
                            task.cancel()
                        except Exception as exc:
                            logger.info(f'{exc[:512]}')

                    logger.info(f'here1.2: {self.info_hash=}')
                    await asyncio.gather(*gather_tasks)

                    logger.info(f'here2: {self.info_hash=}')
                    # await asyncio.gather(*tasks)
                    # logger.info(f'here3: {self.info_hash=}')

                logger.info(f'here4: {self.info_hash=}')
                raise Exception
        except Exception as exc:
            logger.info(f'h5. {exc=}')

        # logger.info(f'here1.3: {self.info_hash=}')
        # async for piece, data in results:
        #     logger.info(f'tr2, {self.info_hash=}')
        #     await collect_result(piece, data, self, to_bytes)

        logger.info(f'surge dwn complete?: {self.info_hash=}')

    async def second_surge_download(
            self,
            missing_pieces,
            to_bytes,
            to_file=None,
            max_peers=100,
            max_requests=5,
            progress_func=print_progress,
    ):

        max_peers = 15
        """Download the files represented by `metadata` to piece.data attribute."""
        peer_id = self.peer_id

        metadata = self.metadata
        info_hash = metadata.info_hash
        # metadata.pieces = pieces

        tasks = set()
        gather_tasks = set()

        try:

            # async with Trackers(
            #         info_hash, peer_id.encode('utf8'), metadata.announce_list, max_peers
            # ) as trackers:

            async with test_with() as tt:
                trackers = None

                results = Channel(max_peers)
                pieces = metadata.pieces
                torrent = Torrent(pieces, missing_pieces, results)

                # try:
                #     await self.dwn_tree_check(
                #         torrent, missing_pieces,
                #     )
                # except Exception as exc:
                #     log_stack.error('ch')

                ident = random.randint(1, 10000)
                try:

                    if missing_pieces:
                        # if True:

                        task = asyncio.create_task(
                            self.dwn_tree_check(torrent, missing_pieces, self.info_hash, ident)
                        )
                        gather_tasks.add(task)

                        asyncio.create_task(
                            progress_func(
                                torrent,
                                trackers,
                                self.info_hash
                            )
                        )
                        # logger.info(f'b.cl')
                    async for piece, data in results:
                        # logger.info(f'cl.1')
                        await collect_result(piece, data, self, to_bytes)
                        # logger.info(f'cl.2')

                    logger.info(f'here0: {self.info_hash=}')
                except Exception:
                    log_stack.error('1')
                finally:

                    logger.info(f'here1.1: {self.info_hash=}')
                    for task in tasks:
                        try:
                            task.cancel()
                        except Exception as exc:
                            logger.info(f'{exc[:512]}')

                    logger.info(f'here1.2: {self.info_hash=}')
                    await asyncio.gather(*gather_tasks)

                    logger.info(f'here2: {self.info_hash=}')
                    # await asyncio.gather(*tasks)
                    # logger.info(f'here3: {self.info_hash=}')

                logger.info(f'here4: {self.info_hash=}')
                raise Exception

        except Exception as exc:
            logger.info(f'h5. {exc=}')

        # logger.info(f'here1.3: {self.info_hash=}')
        # async for piece, data in results:
        #     logger.info(f'tr2, {self.info_hash=}')
        #     await collect_result(piece, data, self, to_bytes)

        logger.info(f'surge dwn complete?: {self.info_hash=}')
