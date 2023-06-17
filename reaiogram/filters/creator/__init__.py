from typing import Union

from aiogram import types

from aiogram.dispatcher.filters import BoundFilter
from config import settings, secrets


class CreatorFilter(BoundFilter):

    """
    Checks if user is creator of a bot.
    id from config file
    """

    def __init__(self, is_creator=True):
        self.is_creator = is_creator

    async def check(self, obj: Union[types.Message]) -> bool:
        user_id = obj.from_user.id

        if hasattr(secrets.creator, 'id'):
            if user_id == secrets.creator.id:
                return self.is_creator
            else:
                return not self.is_creator
        else:
            return not self.is_creator
