# import gc
import os
import time
import string
import random
import asyncio
import binascii

from .rekrbt import (
    Client, DownloadManager,
    PeerConnection,
)

from log import logger

from .default import TorrentDefaultDownload

from .progress.console import print_progress

from ....encoding.stuff import from_bytes_to_hex


class PD:

    def __init__(self, piece, data):
        self.piece = piece
        self.data = data


class TorrentKrbtDownload(
    TorrentDefaultDownload
):
    async def _krbt_download(
            self,
            missing_pieces,
            to_bytes,
            to_file=None,
            max_peers=100,
            max_requests=50,
            progress_func=print_progress,
    ):

        peer_id = self.peer_id

        client = Client()

        # torrent = parse(path)
        # torrent.print_all_info()

        # if torrent.announce.startswith(b'http'):
        if True:
            peers = await client._get_peers(self)
            logger.info(f'{peers=}')

            peers = [('94.41.237.148', 22764), ('31.202.45.165', 39097), ('95.25.149.248', 34553),
                     ('91.219.83.5', 56974), ('62.221.66.15', 16911), ('193.218.141.19', 10643),
                     ('118.93.165.31', 12345), ('212.142.66.38', 51876), ('188.119.113.97', 51198),
                     ('37.150.53.98', 6881), ('94.41.237.148', 22764), ('31.202.45.165', 39097),
                     ('95.25.149.248', 34553), ('91.219.83.5', 56974), ('62.221.66.15', 16911),
                     ('193.218.141.19', 10643), ('118.93.165.31', 12345), ('212.142.66.38', 51876),
                     ('188.119.113.97', 51198), ('37.150.53.98', 6881)]

            peers = [('192.168.55.59', 51198), ]

            logger.info(f'{peers=}')
            # self.tracker = tracker
            # resp = await tracker.announce()
            client.previous = time.time()
            client.download_manager = DownloadManager(self, to_file)

            for peer in peers:
                client.available_peers.put_nowait(peer)

            client.peers = [PeerConnection(
                info_hash=self.metadata.info_hash,
                peer_id=peer_id,
                available_peers=client.available_peers,
                download_manager=client.download_manager,
                on_block_complete=client.on_block_complete)
                for _ in range(2)]

            await client.monitor()

        # for ip_ports in self.extra_peers:
        #     ip, ports = ip_ports
        #     for port in ports:
        #         peer = Peer.from_string(f'{ip}:{port}')
        #         # logger.info(f'{peer=}')
        #
        #         # rnd = ''.join(random.choices(string.ascii_lowercase, k=2))
        #         # rnd2 = ''.join(random.choices(string.ascii_uppercase, k=4))
        #         # peer_id = f'-qB4450-{rnd}Nm{rnd2}PXWj'
        #         rnd = ''.join(random.choices(string.digits, k=2))
        #         peer_id = f'-qB44{rnd}-spNmDQXWPXWj'
        #
        #         tasks.add(
        #             asyncio.create_task(
        #                 download_from_peer_loop(
        #                     torrent, trackers,
        #                     info_hash,
        #                     peer_id.encode('utf8'),
        #                     pieces, max_requests*10,
        #                     self.redis, peer,
        #                     # missing_pieces,
        #                 )
        #             )
        #         )

        #     async for piece, data in results:
        #         if self.valid_piece_data(piece, data):
        #             if to_bytes:
        #                 hex_hash = from_bytes_to_hex(piece.hash)
        #                 i_h = f'{piece.index}_{hex_hash}'
        #                 self.redis.set(i_h, data)
        #                 self.data.append(i_h)
        #         else:
        #             logger.info(f'no valid: {piece=}')
        # finally:
        #
        #     logger.info(f'here: {self.info_hash=}')
        #     for task in tasks:
        #         task.cancel()
        #
        #     # return tasks
        #
        #     logger.info(f'here2: {self.info_hash=}')
        #     await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f'krbt dwn complete?: {self.info_hash=}')
