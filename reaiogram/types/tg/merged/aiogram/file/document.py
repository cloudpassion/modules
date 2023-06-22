from log import logger

from ..types import AiogramDocument

from reaiogram.types.tg.merged.default.file.document import AbstractMergedDocument

from ....chat import MergedTelegramChat


class MergedAiogramDocument(
    AbstractMergedDocument,
):

    unmerged: AiogramDocument

    async def _merge_aiogram_document(self):

        if not self.unmerged:
            return

        # forward_from_chat
        # chat = self.merged_chatMergedTelegramChat(
        #     db=self.db, chat=self.document_chat
        # )
        # self.chat = await chat.merge_chat()

        # logger.info(f'{self.chat=}')
        await self._default_merge_telegram('init_document')

        return self

    async def to_orm(self):
        return await self.db.update_tg_document(
            document=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_document_file_id(
            # file_unique_id=self.file_unique_id
            file_id=self.file_id
        )
