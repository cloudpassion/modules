from log import logger


from .types import AiogramMessage

from reaiogram.types.tg.merged.default.message import AbstractMergedMessage

from reaiogram.types.tg.user import MergedTelegramUser
from reaiogram.types.tg.chat import MergedTelegramChat
from reaiogram.types.tg.file import MergedTelegramDocument


class MergedAiogramMessage(
    AbstractMergedMessage,
):

    unmerged: AiogramMessage

    async def _merge_aiogram_message(self):
        #
        # if not self.unmerged:
        #     return

        await self._default_merge_telegram('m_a_message')

        # message_id
        self.id = self.unmerged.message_id

        self.thread_id = self.unmerged.message_thread_id

        # from
        from_user = MergedTelegramUser(
            db=self.db, user=self.unmerged.from_user
        )
        # logger.info(f'msg:from_user: {from_user=}')
        self.from_user = await from_user.merge_user()

        # chat
        chat = MergedTelegramChat(
            db=self.db, chat=self.unmerged.chat
        )
        # logger.info(f'msg:chat: {chat=}')
        self.chat = await chat.merge_chat()
        # logger.info(f'msg:self.chat: {self.chat=}')
        # logger.info(f'{self.unmerged.chat=}')

        # sender_chat
        sender_chat = MergedTelegramChat(
            db=self.db, chat=self.unmerged.sender_chat
        )
        # logger.info(f'msg:sender_chat: {sender_chat=}')
        self.sender_chat = await sender_chat.merge_chat()

        # forward_from
        forward_from = MergedTelegramUser(
            db=self.db, user=self.unmerged.forward_from
        )
        # logger.info(f'msg:forward_from: {forward_from=}')
        self.forward_from = await forward_from.merge_user()

        # forward_from_chat
        forward_from_chat = MergedTelegramChat(
            db=self.db, chat=self.unmerged.forward_from_chat
        )
        # logger.info(f'msg:forward_from_chat: {forward_from_chat=}')
        self.forward_from_chat = await forward_from_chat.merge_chat()

        # files
        # document_chat = self.unmerged.chat or self.unmerged.sender_chat
        document = MergedTelegramDocument(
            db=self.db, document=self.unmerged.document,
            merged_chat=chat
        #document_chat
        )
        self.document = await document.merge_document()

        return self

    async def to_orm(self):

        await self.db.add_tg_message_history(
            message=self
        )

        return await self.db.update_tg_message(
            message=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_message(
            chat=self.chat,
            from_user=self.from_user,
            sender_chat=self.sender_chat,
            thread_id=self.thread_id,
            id=self.id
        )
