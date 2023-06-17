from log import logger

from .types import AiogramMessage

from ..merged.message import AbstractMergedMessage

from ..user import MergedTelegramUser
from ..chat import MergedTelegramChat
from ..file.document import MergedTelegramDocument


class MergedAiogramMessage(
    AbstractMergedMessage,
):

    unmerged: AiogramMessage

    async def _merge_aiogram_message(self):

        await self._default_merge_telegram()

        # message_id
        self.id = self.unmerged.message_id

        # from
        self.from_user = MergedTelegramUser(
            db=self.db, user=self.unmerged.from_user
        )
        await self.from_user._merge_aiogram_user()

        # chat
        self.chat = MergedTelegramChat(
            db=self.db, chat=self.unmerged.chat
        )
        await self.chat._merge_aiogram_chat()

        # document
        self.document = MergedTelegramDocument(
            db=self.db, document=self.unmerged.document
        )
        await self.document._merge_aiogram_document(
            chat=self.chat
        )

    async def to_orm(self):

        await self.db.add_tg_message_history(
            message=self
        )

        return await self.db.update_tg_message(
            message=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_message_id(
            chat=self.chat, id=self.id
        )
