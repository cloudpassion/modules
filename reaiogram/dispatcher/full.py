from .listen import ReviewUpdateDispatcher
from reaiogram.handlers.dispatcher.orm import OrmDispatcher


class FullDispatcher(
    OrmDispatcher,
    ReviewUpdateDispatcher,
):
    pass
