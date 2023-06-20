from typing import Optional

from .default import DefaultRouter


class FullRouter(
    DefaultRouter,

):
    def __init__(self, *, name: Optional[str] = None) -> None:

        _hex = hex(id(self))[4:]
        self.name = f'{name}_{_hex}' if name else hex(id(self))
        super().__init__(name=self.name)
