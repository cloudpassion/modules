import dataclasses
import gc

import psutil

from typing import List, Optional
import surge.bencoding as bencoding

from surge.metadata import (
    Piece as DefaultPiece,
    Metadata as DefaultMetadata,
    File, yield_available_pieces
)

from ...encoding.stuff import from_bytes_to_hex

from log import logger


# @dataclasses.dataclass
# class Piece:
@dataclasses.dataclass(frozen=True)
class Piece(DefaultPiece):
    """Piece metadata."""

    index: int
    begin: int  # Absolute offset.
    length: int
    hash: bytes  # SHA-1 digest of the piece's data.

    data: bytes
    completed: bool


# How to include field from AbstractTorrent to this dataclass??
# If set is as subclass, fields are ignores
# at this time I set field two times
@dataclasses.dataclass
class Metadata(
    # DefaultMetadata,
):

    announce: str
    info: str

    info_hash: bytes
    announce_list: List[str]
    url_list: List[str]
    pieces: List[Piece]
    files: List[File]

    created_by: str
    creation_date: int
    comment: str
    publisher: str
    publisher_url: str

    @classmethod
    def from_bytes(cls, raw_metadata):

        # ret = Metadata
        # ret = ret.from_bytes(raw_metadata)

        # ret = super(DefaultMetadata, cls).from_bytes(raw_metadata)

        ret = DefaultMetadata
        ret = ret.from_bytes(raw_metadata)
        # ret = super(Metadata, cls).from_bytes(raw_metadata)

        d = bencoding.decode(raw_metadata)
        super_keys = ('info_hash', 'announce_list', 'pieces', 'files')
        all_keys = cls.__annotations__.keys()

        for key in d.keys():
            if key in super_keys:
                continue

            str_key = key.decode('utf8').replace('-', '_').replace(' ', '_')
            try:
                setattr(ret, str_key, d[key].decode('utf8'))
            except AttributeError:
                setattr(ret, str_key, d[key])

        # for key in super_keys:
        #     setattr(ret, key, getattr(ret, key))

        for key in all_keys:
            if not hasattr(ret, key):
                setattr(ret, key, None)

        # pieces
        # Piece(i, begin, end - begin, hashes[j : j + 20])
        pieces = []
        for p in ret.pieces:
            if from_bytes_to_hex(p.hash) == '6a521e1d2a632c26e53b83d2cc4b0edecfc1e68c':
                logger.info(f'{p=}')
                logger.info(f'{p.hash=}')

            # piece = Piece
            # piece(p.index, p.begin, p.length, p.hash, b'', False)
            # pieces.append(piece)
            pieces.append(
                Piece(
                    p.index,
                    p.begin,
                    p.length,
                    p.hash,
                    b'',
                    False,
                )
            )

        #     Piece(
        #         p.index,
        #         p.begin,
        #         p.length,
        #         p.hash,
        #         b'',
        #         False,
        #     ) for p in ret.pieces
        # ]
        setattr(ret, 'pieces', pieces)

        return cls(
            ret.announce,
            ret.info,
            ret.info_hash,
            ret.announce_list,
            ret.url_list,
            ret.pieces,
            ret.files,
            ret.created_by,
            ret.creation_date,
            ret.comment,
            ret.publisher,
            ret.publisher_url
        )


class DefaultTorrentPiece:

    piece: Piece
    metadata: Metadata

    #db
    info_hash: str
    version: int
    length: int
    index: int
    begin: int
    resume_data: str

    peer_id: str
    parsed: bool
    data: bytes
    completed: bool

    def __init__(
            self,
            piece: Piece,
            metadata: Metadata,
            peer_id: str,
    ):
        self.piece = piece
        self.metadata = metadata
        self.peer_id = peer_id

        self.parsed = False
        self.data = b''
        self.completed = False

        self.parse()


def test_piece_default():

    return

    mem_pre = psutil.Process().memory_info().rss

    with open('test10.torrent', 'rb') as f:

        cl = Metadata
        p = cl.from_bytes(f.read())
        d = f.read()
        p = Piece(
            1, 1, 1, b'',
            d*20*12312312312312,
            # b'asdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfadsfasdfadsfasdfasdfasdfasdf',
            False
        )
        # setattr(p, 'data', )
        # p.data = d+d+d+d+d+d+d+d+d
        logger.info(f'{p=}')
        mem_do = psutil.Process().memory_info().rss

        del p.data

        gc.collect()

        mem_after = psutil.Process().memory_info().rss

        logger.info(f'{p=}\n{mem_pre}\n{mem_do}\n{mem_after}')
    #
    # logger.info(f'{p=}')
    # logger.info(f'{cl.pieces=}')
    # set(list(cl.pieces))


def test_available():

    return

    from ...encoding.stuff import from_bytes_to_hex

    # h = from_bytes_to_hex(b'Y(n=\x01$>m\x01\xfa\x82\xd3~6\xbe@0\xbf\x03T')
    # logger.info(f'{h=}')
    # return
    with open('test18.torrent', 'rb') as f:
        metadata = Metadata.from_bytes(f.read())

    folder = '/exm/wd1000blk/temp_tg/out'
    missing_pieces = set(metadata.pieces)
    for piece in yield_available_pieces(metadata.pieces, folder, metadata.files):
        missing_pieces.remove(piece)

    logger.info(f'{missing_pieces=}')
