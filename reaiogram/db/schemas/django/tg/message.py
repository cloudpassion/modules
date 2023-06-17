from typing import Union

from log import log_stack, logger

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgMessage as DjangoTgMessage,
    TgMessageHistory as DjangoTgMessageHistory,
)

from reaiogram.db.schemas.django.tg.default import DefaultDjangoORM

from .....db.types.message import MergedAiogramMessage, MergedTelegramMessage

# from asgiref.sync import sync_to_async, async_to_sync


class DjangoORMTgMessage(
    DefaultDjangoORM
):

    async def select_tg_message_id(
            self, chat: MergedTelegramMessage, id: int
    ):

        message = DjangoTgMessage()

        self.set_select(
            data=message,
            select_kwargs={
                'chat': chat,
                'id': id,
            },
            set_keys=True,
        )
        logger.info(f'here32')
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

        self.set_select(
            data=message,
            select_kwargs={
                'chat': chat,
                'id': message.id,
            }
        )
        return await self.update_one(
            data=message, db_class=DjangoTgMessage
        )
