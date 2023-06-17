from typing import Union

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgDocument as DjangoTgDocument
)

from log import log_stack, logger

from reaiogram.db.schemas.django.tg.default import DefaultDjangoORM

from ......db.types import MergedAiogramDocument, MergedTelegramDocument

# from asgiref.sync import sync_to_async, async_to_sync


class DjangoORMTgFile(
    DefaultDjangoORM
):

    async def select_tg_file_unique_id(
            self, file_unique_id: str,
            db_class: Union[
                type(DjangoTgDocument),
            ]
    ):

        data = DjangoTgDocument()

        self.set_select(
            data=data,
            select_kwargs={
                'file_unique_id': file_unique_id,
            },
            set_keys=True,
        )
        logger.info(f'here35')
        return await self.select_one(
            data=data, db_class=db_class
        )

    async def update_tg_file(
            self, data: Union[
                MergedTelegramDocument
            ],
            db_class: Union[
                type(DjangoTgDocument),
            ]
    ) -> DjangoTgDocument:

        logger.info(f'here35')
        self.set_select(
            data=data,
            select_kwargs={
                'file_unique_id': data.file_unique_id
            }
        )
        return await self.update_one(
            data=data, db_class=db_class,
        )
