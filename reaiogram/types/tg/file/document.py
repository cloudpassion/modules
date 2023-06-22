from log import logger

from reaiogram.types.tg.merged.aiogram.types import AiogramDocument
from reaiogram.types.tg.merged.aiogram.file.document import MergedAiogramDocument

from ...django import (
    TgDocument
)


class MergedTelegramDocument(
    # MergedPyrogramMessage,
    MergedAiogramDocument,
):

    def __init__(self, db, document, merged_chat=None):
        self.unmerged = document
        self.db_class = TgDocument
        self.db = db
        self.chat = merged_chat

    async def merge_document(self):
        if not self.unmerged:
            # logger.info(f'no document {hex(id(self))=}')
            return

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramDocument,
        )):
            await self._merge_aiogram_document()

        await self._convert_to_orm()
        return self

