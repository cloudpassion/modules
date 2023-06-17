from typing import Union

from log import log_stack, logger

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgChat as DjangoTgChat,
    TgChatHistory as DjangoTgChatHistory,
)

from reaiogram.db.schemas.django.tg.default import DefaultDjangoORM

from .....db.types.chat import MergedAiogramChat, MergedTelegramChat


class DjangoORMTgChat(
    DefaultDjangoORM
):

    async def select_tg_chat_id(self, id: int) -> DjangoTgChat:

        chat = DjangoTgChat()
        self.set_select(
            data=chat,
            select_kwargs={'id': id},
            set_keys=True,
        )
        logger.info(f'here32')
        return await self.select_one(
            data=chat, db_class=DjangoTgChat
        )

    async def add_tg_chat_history(
            self, chat: Union[
                MergedTelegramChat
            ],
    ):

        return await self.add_one_history(
            data=chat, db_class=DjangoTgChatHistory
        )

    async def update_tg_chat(
            self, chat: Union[
                MergedAiogramChat,
                MergedTelegramChat,
            ],
    ):

        logger.info(f'here333')
        return await self.update_one(
            data=chat, db_class=DjangoTgChat
        )
