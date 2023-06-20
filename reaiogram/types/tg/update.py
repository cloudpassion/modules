from .merged.aiogram.types import AiogramUpdate
from .merged.aiogram.update import MergedAiogramUpdate

from ...types.django import (
    TgUpdate,
)


class MergedTelegramUpdate(
    # MergedPyrogramMessage,
    MergedAiogramUpdate,
):

    def __init__(self, db, update=None, merged_bot=None):
        self.merged_bot = merged_bot
        self.unmerged = update
        self.db_class = TgUpdate
        self.db = db

    async def merge_update(self):
        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUpdate,
        )):
            return await self._merge_aiogram_update()
