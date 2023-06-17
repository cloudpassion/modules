from reaiogram.dispatcher.default import Dispatcher
from .users import (
    EchoHandler,
)
from .blocked import BlockedHandler
from .creator import BotCreatorHandler
# from .lesson import (
#     LessonMenuHandler,
#     LessonInlineHandler,
#     LessonUserMenuHandler,
#     LessonUserMenuBuyItemHandler
# )
from .chatgrab import ChatGrabHandler
# from .task5 import Task5Handler


class CreatorHandler(
    BotCreatorHandler
):
    pass


class DefaultHandler(

    ChatGrabHandler,
    BlockedHandler,
):
    pass


class AdminsHandler(
    DefaultHandler
):
    pass


class UsersHandler(
    DefaultHandler,
    # Task5Handler,
    EchoHandler,
    # LessonUserMenuHandler,
    # LessonUserMenuBuyItemHandler
):
    pass


class ChannelsHandler(
    DefaultHandler
):
    pass
