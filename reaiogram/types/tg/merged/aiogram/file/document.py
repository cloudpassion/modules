from log import logger

from ..types import AiogramDocument

from reaiogram.types.tg.merged.default.file.document import AbstractMergedDocument

from ....chat import MergedTelegramChat


class MergedAiogramDocument(
    AbstractMergedDocument,
):

    unmerged: AiogramDocument

    async def _merge_aiogram_document(self):
        #
        # if not self.unmerged:
        #     return

        # forward_from_chat
        # chat = self.merged_chatMergedTelegramChat(
        #     orm=self.orm, chat=self.document_chat
        # )
        # self.chat = await chat.merge_chat()

        # logger.info(f'{self.chat=}')

        return self

    async def to_orm(self):
        return await self.orm.update_tg_document(
            document=self,
        )

    async def from_orm(self):
        return await self.orm.select_tg_document_file_id(
            # file_unique_id=self.file_unique_id
            file_id=self.file_id
        )
