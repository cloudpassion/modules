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
        """
        Register event handler
        """
        if kwargs:
            raise UnsupportedKeywordArgument(
                "Passing any additional keyword arguments to the registrar method "
                "is not supported.\n"
                "This error may be caused when you are trying to register filters like in 2.x "
                "version of this framework, if it's true just look at correspoding "
                "documentation pages.\n"
                f"Please remove the {set(kwargs.keys())} arguments from this call.\n"
            )

        if flags is None:
            flags = {}

        for item in filters:
            if isinstance(item, Filter):
                item.update_handler_flags(flags=flags)

        self.handlers.appendleft(
            HandlerObject(
                callback=callback,
                filters=[FilterObject(filter_) for filter_ in filters],
                flags=flags,
            )
        )

        return callback


# class FullTelegramEventObserverForThread(DefaultTelegramEventObserver):
#     pass

