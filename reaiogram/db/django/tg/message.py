from typing import Union

from log import logger

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgMessage as DjangoTgMessage,
    TgMessageHistory as DjangoTgMessageHistory,
)

from .default import DefaultDjangoTgORM

from ....types.tg.user import MergedTelegramUser
from ....types.tg.chat import MergedTelegramChat
from ....types.tg.message import MergedTelegramMessage

# from asgiref.sync import sync_to_async, async_to_sync


class DjangoORMTgMessage(
    DefaultDjangoTgORM
):

    async def select_tg_message(
            self,
            chat: MergedTelegramChat,
            from_user: MergedTelegramUser,
            sender_chat: MergedTelegramChat,
            thread_id: int,
            id: int,
    ):
        message = DjangoTgMessage()

        chat = await self.select_tg_chat_id(
            id=chat.id
        )

        try:
            from_user = await self.select_tg_user_id(
                id=from_user.id
            )
        except AttributeError:
            from_user = None

        try:
            sender_chat = await self.select_tg_chat_id(
                id=sender_chat.id
            )
        except AttributeError:
            sender_chat = None

        self.set_select(
            data=message,
            select_kwargs={
                'chat': chat,
                'from_user': from_user,
                'sender_chat': sender_chat,
                'thread_id': thread_id,
                'id': id,
            },
            set_keys=True,
        )
        return await self.select_one(
            data=message, db_class=DjangoTgMessage
        )

    async def add_tg_message_history(
            self, message: Union[
                MergedTelegramMessage
            ],
    ):
        return await self.add_one_history(
            data=message, db_class=DjangoTgMessageHistory
        )

    async def update_tg_message(
            self, message: Union[
                MergedTelegramMessage
            ],
    ) -> DjangoTgMessage:

        chat = await self.select_tg_chat_id(
            id=message.chat.id
        )

        try:
            from_user = await self.select_tg_user_id(
                id=message.from_user.id
            )
        except AttributeError:
            from_user = None

        try:
            sender_chat = await self.select_tg_chat_id(
                id=message.sender_chat.id
            )
        except AttributeError:
            sender_chat = None

        self.set_select(
            data=message,
            select_kwargs={
                'chat': chat,
                'from_user': from_user,
                'sender_chat': sender_chat,
                'thread_id': message.thread_id,
                'id': message.id,
            }
        )
        return await self.update_one(
            data=message, db_class=DjangoTgMessage
        )
