from .file import TorrentF
from .piece import TorrentPieceF
from .stuff import TorrentStuff


class TorrentFile(
    TorrentF,
    TorrentStuff,
):
    pass


class TorrentPiece(
    TorrentPieceF
):
    pass


