from reaiogram.dispatcher.default import Dispatcher
from .creator import CreatorFilter
from .task5 import NotRegisteredFilter


def register_filters(dp: Dispatcher):
    dp.filters_factory.bind(CreatorFilter)
    dp.filters_factory.bind(NotRegisteredFilter)
