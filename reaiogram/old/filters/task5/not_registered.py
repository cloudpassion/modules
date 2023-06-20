from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from log import logger
from config import settings, secrets
from reaiogram.db import SqlDatabase


class NotRegisteredFilter(BoundFilter):

    """
    Checks if user is creator of a bot.
    id from config file
    """

    def __init__(self, is_creator=True):
        self.registered = False

    async def check(self, obj: Union[types.Message, types.CallbackQuery]) -> bool:
        user_id = obj.from_user.id

        sql_user = await SqlDatabase.select_user(user_id=user_id)
        logger.debug(f'{sql_user=}')

        if sql_user:
            if not sql_user.registered:
                return not False

            self.registered = True
            return not True

        return not False
