import asyncio
import os
import pytest
import tracemalloc

from log import logger

from .. import TorrentF as TorrentFile
from ..default import Metadata
from ..rw.merge import yield_available_pieces
from ....encoding.stuff import from_bytes_to_hex




@pytest.mark.asyncio
async def test_piece_download():

    return
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

            with open('test15.torrent', 'rb') as f:
                metadata = Metadata.from_bytes(f.read())

            folder = '/exm/wd1000blk/temp_tg/out'
            missing_pieces = set(metadata.pieces)
            pieces_to_check = []

            for p in metadata.pieces:
                if p.hash != b'Y(n=\x01$>m\x01\xfa\x82\xd3~6\xbe@0\xbf\x03T':
                    continue

                pieces_to_check.append(p)

            for piece in yield_available_pieces(
                    metadata.pieces, folder, metadata.files,
                    check_only=pieces_to_check,
            ):
                # logger.info(f'remove {piece=}')
                missing_pieces.remove(piece)

            logger.info(f'{missing_pieces=}')


@pytest.mark.asyncio
async def test_some_checks():

    for n in (
            18,
    ):
        file_path = f'test{n}.torrent'
        if not os.path.isfile(file_path):
            continue

        with open(file_path, 'rb') as f:

            cl = TorrentFile(file=f)
            cl.parse()

            pieces_to_check = []

            for p in cl.metadata.pieces:
                # if from_bytes_to_hex(p.hash) != '9e5ac113f3c3d2599647aeac86cdd063b49505f5':
                #     continue

                # logger.info(f'{p=}')
                pieces_to_check.append(p)

            folder = '/exm/wd1000blk/temp_tg/out'
            missing_pieces = set(cl.metadata.pieces)
            for piece in yield_available_pieces(
                    cl.metadata.pieces, folder, cl.metadata.files, pieces_to_check
            ):
                missing_pieces.remove(piece)

            logger.info(f'{missing_pieces=}')
                    # yield_available_pieces(piece)

            return
