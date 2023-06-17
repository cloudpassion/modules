from .default import Dispatcher
from ..handlers import (
    UsersHandler,
    ChannelsHandler,
    AdminsHandler,
    CreatorHandler
)


class FullDispatcher(
    CreatorHandler,
    AdminsHandler,
    UsersHandler,
    ChannelsHandler,
    Dispatcher,
):
    pass
