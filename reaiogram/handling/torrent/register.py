from .router import torrent_bot_router
from .middlewares.file import register_torrent_file_prepare
from .handlers.merge import _
from .handlers.download import _


def register_torrent_router(dp):

    # pre
    register_torrent_file_prepare(torrent_bot_router)

    # handlers
    # register_torrent_merge_handler(torrent_bot_router)

    dp.include_router(torrent_bot_router)
