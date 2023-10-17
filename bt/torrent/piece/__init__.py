
from .parse import TorrentPieceParse
from .download import TorrentPieceDownload


class TorrentPieceF(
    TorrentPieceParse,
    TorrentPieceDownload
):
    pass
