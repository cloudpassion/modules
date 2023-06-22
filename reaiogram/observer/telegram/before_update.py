from collections import deque

from typing import Any, Dict, Optional

from aiogram.exceptions import UnsupportedKeywordArgument
from aiogram.filters.base import Filter
from aiogram.dispatcher.event.handler import CallbackType, FilterObject, HandlerObject

from .default import DefaultTelegramEventObserver


class BeforeUpdateTelegramEventObserver(
    DefaultTelegramEventObserver
):

    handlers: deque

    def left_register(
            self,
            callback: CallbackType,
            *filters: CallbackType,
            flags: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> CallbackType:
        cb = super(BeforeUpdateTelegramEventObserver, self).register(
            callback, *filters, *flags, **kwargs
        )
        handler = self.handlers.pop()
        self.handlers.appendleft(handler)

        return cb


# class FullTelegramEventObserverForThread(DefaultTelegramEventObserver):
#     pass

