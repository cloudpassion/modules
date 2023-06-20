from aiogram.types import Message
from aiogram.dispatcher.event.bases import SkipHandler

from log import logger

from reaiogram.default.router import Router

from reaiogram.dispatcher.default import ExtraDispatcher


class OrmDispatcher(ExtraDispatcher):

    router: Router

    # better handle it at middleware

    async def _append_handler_0_orm(self):

        @self.edited_message()
        @self.message()
        async def save_message_to_orm(*args, **kwargs):
            # await self.orm.database_message(message)
            raise SkipHandler()


