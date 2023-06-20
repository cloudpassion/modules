from .next_update import register_next_update_middleware
from .orm import register_orm_middleware


def register_middlewares(dp):
    register_next_update_middleware(dp)
    register_orm_middleware(dp)
