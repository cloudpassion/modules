from .listen_update import ReviewUpdateDispatcher
# from reaiogram.handlers.dispatcher.orm import OrmDispatcher
from ..handling.dispatcher.outer import OuterMiddlewareDispatcher
# from reaiogram.handlers.router.torrent.router import TorrentDispatcher


class FullDispatcher(
    # OrmDispatcher,
    OuterMiddlewareDispatcher,
    ReviewUpdateDispatcher,
    # TorrentDispatcher
):
    pass
