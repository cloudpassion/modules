from .rights import register_rights_router
from .orm import register_update_to_orm_router


def register_main_router(router):
    register_update_to_orm_router(router)
    register_rights_router(router)
