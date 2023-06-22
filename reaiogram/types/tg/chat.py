from log import logger

from .merged.aiogram.types import AiogramChat
from .merged.aiogram.chat import MergedAiogramChat

from ...types.django import (
    TgChat,
)


class MergedTelegramChat(
    # MergedPyrogramMessage,
    MergedAiogramChat,
):

    def __init__(self, db, chat):
        self.unmerged = chat
        self.db_class = TgChat
        self.db = db

    async def merge_chat(self):

        if self.unmerged is None:
            # logger.info(f'no chat {hex(id(self))=}')
            return

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramChat,
        )):
            await self._merge_aiogram_chat()

        await self._convert_to_orm()
        return self
