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

        # message_id
        self.id = self.unmerged.message_id

        self.thread_id = self.unmerged.message_thread_id

        # from
        from_user = MergedTelegramUser(
            orm=self.orm, user=self.unmerged.from_user,
            skip_orm=self.skip_orm
        )
        # logger.info(f'msg:from_user: {from_user=}')
        self.from_user = await from_user.merge_user()

        # chat
        chat = MergedTelegramChat(
            orm=self.orm, chat=self.unmerged.chat,
            skip_orm=self.skip_orm
        )
        # logger.info(f'msg:chat: {chat=}')
        self.chat = await chat.merge_chat()
        # logger.info(f'msg:self.chat: {self.chat=}')
        # logger.info(f'{self.unmerged.chat=}')

        # sender_chat
        sender_chat = MergedTelegramChat(
            orm=self.orm, chat=self.unmerged.sender_chat,
            skip_orm=self.skip_orm
        )
        # logger.info(f'msg:sender_chat: {sender_chat=}')
        self.sender_chat = await sender_chat.merge_chat()

        # forward_from
        forward_from = MergedTelegramUser(
            orm=self.orm, user=self.unmerged.forward_from,
            skip_orm=self.skip_orm
        )
        # logger.info(f'msg:forward_from: {forward_from=}')
        self.forward_from = await forward_from.merge_user()

        # forward_from_chat
        forward_from_chat = MergedTelegramChat(
            orm=self.orm, chat=self.unmerged.forward_from_chat,
            skip_orm=self.skip_orm
        )
        # logger.info(f'msg:forward_from_chat: {forward_from_chat=}')
        self.forward_from_chat = await forward_from_chat.merge_chat()

        # files
        document = MergedTelegramDocument(
            orm=self.orm, document=self.unmerged.document,
            skip_orm=self.skip_orm
        )
        self.document = await document.merge_document()

        return self

    async def to_orm(self):

        await self.orm.add_tg_message_history(
            message=self
        )

        return await self.orm.update_tg_message(
            message=self,
        )

    async def from_orm(self):
        return await self.orm.select_tg_message(
            chat=self.chat,
            from_user=self.from_user,
            sender_chat=self.sender_chat,
            thread_id=self.thread_id,
            id=self.id
        )
