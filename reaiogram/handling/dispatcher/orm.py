from aiogram.types import Message
from aiogram.dispatcher.event.bases import SkipHandler

from log import logger

from reaiogram.dispatcher.default import ExtraDispatcher


class OrmDispatcher(ExtraDispatcher):

    # better handle saving all messages to db in middlewares
    # at outer middleware
    #
    # middlewares handling earlier than filters and handlers which
    # may be initiating skipping next handlers

    async def _append_handler_0_orm(self):

        @self.edited_message()
        @self.message()
        async def save_message_to_orm(
                message,
                bot,
                event_from_user,
                event_chat,
                fsm_storage,
                state,
                raw_state,
                handler,
                event_update,
                event_router,
                **kwargs,
        ):
            # await self.orm.database_message(message)
            raise SkipHandler()


