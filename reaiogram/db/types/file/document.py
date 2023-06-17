from ..aiogram.types import AiogramDocument
from ..aiogram.file.document import MergedAiogramDocument

from ...types.django import (
    TgDocument
)


class MergedTelegramDocument(
    # MergedPyrogramMessage,
    MergedAiogramDocument,
):

    def __init__(self, db, document=None):
        self.unmerged = document
        self.db_class = TgDocument
        self.db = db

    async def merge_document(self):
        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramDocument,
        )):
            return await self._merge_aiogram_document()
