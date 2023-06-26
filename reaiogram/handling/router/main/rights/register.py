from .router import rights_router

from .all import register_rights_all


def register_rights_router(router):

    register_rights_all(rights_router)

    router.include_router(rights_router)
