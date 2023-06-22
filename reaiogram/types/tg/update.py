from log import logger

from .merged.aiogram.types import AiogramUpdate
from .merged.aiogram.update import MergedAiogramUpdate

from ...types.django import (
    TgUpdate,
)


class MergedTelegramUpdate(
    # MergedPyrogramMessage,
    MergedAiogramUpdate,
):

    def __init__(
            self, db, update, merged_bot,
            **kwargs,
    ):

        self.db = db
        self.unmerged = update
        self.db_class = TgUpdate
        self.bot = merged_bot

        # optional any of message from update
        for key, value in kwargs.items():
            # logger.info(f'{key=} with {value=}')
            setattr(self, f'merged_{key}', value)

    async def merge_update(self):

        if self.unmerged is None:
            # logger.info(f'no update {hex(id(self))=}')
            return None

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUpdate,
        )):
            await self._merge_aiogram_update()

        await self._convert_to_orm()
        return self
