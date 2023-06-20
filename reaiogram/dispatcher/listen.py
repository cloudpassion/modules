from typing import Any

from aiogram.types import Update
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types.update import UpdateTypeLookupError

from log import logger

from .default import ExtraDispatcher


class ReviewUpdateDispatcher(ExtraDispatcher):

    # rewrited function for handling next registered
    # update event
    # in default variant on 19 June 2023
    # Router not handling update event type and
    # Dispather handle only one update observer and initiate return
    #
    # if delete return all registered callable function
    # via dispatcher.update.register handling
    #
    # if more that one, need raise SkipHandler() at end
    # for handling next
    async def _listen_update(self, update: Update, **kwargs: Any) -> Any:
        await super()._listen_update(update, **kwargs)
        logger.info(f'skip_handler_dispatcher')
        raise SkipHandler()
