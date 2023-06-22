from .router import torrent_bot_router

from .file import register_torrent_file_prepare


def register_torrent_router(dp):

    register_torrent_file_prepare(torrent_bot_router)

    dp.include_router(torrent_bot_router)
