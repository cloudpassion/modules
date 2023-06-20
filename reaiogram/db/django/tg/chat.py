from typing import Union

from log import logger

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgChat as DjangoTgChat,
    TgChatHistory as DjangoTgChatHistory,
)

from .default import DefaultDjangoTgORM

from reaiogram.types import MergedAiogramChat, MergedTelegramChat


class DjangoORMTgChat(
    DefaultDjangoTgORM
):

    async def select_tg_chat_id(self, id: int) -> DjangoTgChat:

        chat = DjangoTgChat()
        self.set_select(
            data=chat,
            select_kwargs={'id': id},
            set_keys=True,
        )
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

        return await self.update_one(
            data=chat, db_class=DjangoTgChat
        )
