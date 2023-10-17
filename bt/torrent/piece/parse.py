import hashlib
import binascii
from torrent_parser import encode
import surge.bencoding as bencoding

from base64 import b64encode, b64decode

from log import logger

from .default import DefaultTorrentPiece


class TorrentPieceParse(
    DefaultTorrentPiece
):

    def gen_hash(self):
        _hash = binascii.hexlify(self.piece.hash).decode()
        # logger.info(f'{_hash}')

        # _hash = hashlib.sha1(self.piece.hash).hexdigest()
        # _hash = binascii.hexlify(hashlib.sha1(self.piece.hash).digest()).decode()
        self.info_hash = _hash
        return _hash

    def parse(self):

        if self.parsed:
            return

        self.gen_hash()
        self.length = self.piece.length
        self.index = self.piece.index
        self.parsed = True


def test_piece():

    from .. import TorrentFile

    with open('test2.torrent', 'rb') as f:

        cl = TorrentFile(file=f)
        cl.metadata.from_bytes(cl.bytes_data)

        logger.info(f'{dir(cl.metadata)}')

        piece = TorrentPieceParse(piece=cl.metadata.pieces[0])
        logger.info(piece.gen_hash())
