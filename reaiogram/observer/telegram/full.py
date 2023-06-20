from collections import deque

from reaiogram.default.router import Router

from .before_update import BeforeUpdateTelegramEventObserver


class FullTelegramEventObserver(
    BeforeUpdateTelegramEventObserver
):

    def __init__(self, router: Router, event_name: str) -> None:
        super().__init__(router, event_name)
        self.handlers = deque()
