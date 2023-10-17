import asyncio
import os
import pytest
import tracemalloc

from log import logger


from .. import TorrentF as TorrentFile
from ....encoding.stuff import from_bytes_to_hex




@pytest.mark.asyncio
async def test_piece_download():

    tracemalloc.start()
    # from ..
    # from .parse import TorrentPieceParse
    #
    # class TempTorrentPiece(
    #     TorrentPieceDownload,
    #     TorrentPieceParse,
    # ):
    #     pass

    for n in (
            15,
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

            l = cl.metadata.pieces[0].length
            for p in cl.metadata.pieces:
                if p.length != l:
                    logger.info(f'{p.length}, {p=}')

            missing_pieces = set(cl.metadata.pieces)
            for p in cl.metadata.pieces:

                if p.hash == b'Y(n=\x01$>m\x01\xfa\x82\xd3~6\xbe@0\xbf\x03T':
                    continue

                missing_pieces.remove(p)

            logger.info(f'{missing_pieces=}')

            asyncio.create_task(
                cl.download(
                    # cl.metadata.pieces,
                    missing_pieces,
                    to_bytes=True
                )
            )
            i = 0
            while True:
                await asyncio.sleep(10)
                i += 1

                if i % 10 == 0:
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics('lineno')
                    logger.info("[ Top 10 ]")
                    for stat in top_stats[:10]:
                        logger.info(f'{stat}')

            return

            piece = TempTorrentPiece(
                piece=cl.metadata.pieces[0],
                metadata=cl.metadata,
                peer_id=cl.gen_peer_id()
            )

            await piece.download(to_bytes=True)
            logger.info(f'{piece.valid_piece_data(piece.data)}')
