import os
import asyncio
import binascii

from surge.metadata import (
    valid_piece_data,
)
from surge.protocol import (
    Torrent as SurgeTorrent,
    Channel,
    download_from_peer_loop,
    print_progress,
)

from bt.tracker.resurge import Trackers

from log import logger

from .default import DefaultTorrentPiece


class TorrentPieceDownload(
    DefaultTorrentPiece
):

    def valid_piece_data(self, data):
        return valid_piece_data(self.piece, data)

    async def download(
            self,
            to_bytes=False, to_file=False,
            variant='surge',
    ):
        if not to_bytes and not to_file:
            logger.info(f'need set to_bytes or to_file')
            return

        if variant == 'surge':
            await self._surge_download(to_bytes, to_file)

    async def _surge_download(
            self,
            to_bytes,
            to_file=None,
            max_peers=50,
            max_requests=50,
    ):

        """Download the files represented by `metadata` to data attribute."""
        metadata = self.metadata
        peer_id = self.peer_id
        info_hash = metadata.info_hash
        async with Trackers(
                info_hash, peer_id, metadata.announce_list, max_peers
        ) as trackers:
            # pieces = metadata.pieces
            # logger.info(f'{len(pieces)=}, {pieces=}')
            pieces = [self.piece, ]
            results = Channel(max_peers)
            torrent = SurgeTorrent(pieces, pieces, results)
            tasks = set()
            try:
                for _ in range(max_peers):
                    tasks.add(
                        asyncio.create_task(
                            download_from_peer_loop(
                                torrent, trackers,
                                info_hash,
                                peer_id.encode('utf8'),
                                pieces, max_requests
                            )
                        )
                    )
                tasks.add(asyncio.create_task(print_progress(torrent, trackers)))
                async for piece, data in results:
                    if self.valid_piece_data(data):
                        self.data = data
                        self.completed = True
                    else:
                        logger.info(f'data not valid: {piece=}')
            finally:
                for task in tasks:
                    task.cancel()

                await asyncio.gather(*tasks, return_exceptions=False)


import pytest


@pytest.mark.asyncio
async def test_piece_download():

    from .. import TorrentFile
    from .parse import TorrentPieceParse

    class TempTorrentPiece(
        TorrentPieceDownload,
        TorrentPieceParse,
    ):
        pass

    for n in (
            10,
    ):
        file_path = f'test{n}.torrent'
        if not os.path.isfile(file_path):
            continue

        with open(file_path, 'rb') as f:

            cl = TorrentFile(file=f)
            cl.parse()

            cl.metadata.announce_list.extend(
                ['http://retracker.local/announce',
                'http://tor2merun.local/announce',
                'http://qbwin.local/announce',
                'http://qb.local/announce']
            )
            piece = TempTorrentPiece(
                piece=cl.metadata.pieces[0],
                metadata=cl.metadata,
                peer_id=cl.gen_peer_id()
            )

            await piece.download(to_bytes=True)
            logger.info(f'{piece.valid_piece_data(piece.data)}')
