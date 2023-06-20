from ..types import AiogramDocument

from reaiogram.types.tg.merged.default.file.document import AbstractMergedDocument


class MergedAiogramDocument(
    AbstractMergedDocument,
):

    unmerged: AiogramDocument

    async def _merge_aiogram_document(self, chat):

        self.chat = chat
        await self._default_merge_telegram()

    async def to_orm(self):
        return await self.db.update_tg_document(
            document=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_document_file_unique_id(
            file_unique_id=self.file_unique_id
        )
