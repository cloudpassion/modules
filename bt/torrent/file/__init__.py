
from .parse import TorrentParse
from .download import TorrentDownload
from .rw import TorrentReadWrite


class TorrentF(
    TorrentParse,
    TorrentDownload,
    TorrentReadWrite,
):
    pass
