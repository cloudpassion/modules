from ...default.router import Router

from .torrent import register_torrent_router
from reaiogram.handlers.router.main import register_main_router


def register_routers(dp):

    # main router
    router = Router(name='main')

    register_main_router(router)

    dp.include_router(
        router=router,
    )

    # other
    # torrent bot pre handlers
    register_torrent_router(dp)

    # new here

