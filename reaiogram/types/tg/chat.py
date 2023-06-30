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

    def __init__(self, orm, chat, skip_orm=False):
        self.unmerged = chat
        self.orm = orm
        self.skip_orm = skip_orm

    async def merge_chat(self):

        if self.unmerged is None:
            # logger.info(f'no chat {hex(id(self))=}')
            return

        await self._default_merge_telegram('init_chat')

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramChat,
        )):
            await self._merge_aiogram_chat()

        if not self.skip_orm:
            await self._convert_to_orm()

        return self
