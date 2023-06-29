from .listen_update import ReviewUpdateDispatcher
from ..handling.dispatcher.orm import OrmDispatcher
from ..handling.dispatcher.outer import OuterMiddlewareDispatcher
from .new_bot import NewBotDispatcher

from reaiogram.handling.torrent.dispatcher import TorrentDispatcher


class FullDispatcher(
    OuterMiddlewareDispatcher,
    OrmDispatcher,

    ReviewUpdateDispatcher,

    NewBotDispatcher,

    TorrentDispatcher,
):
    pass
