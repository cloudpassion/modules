from typing import Union

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgDocument as DjangoTgDocument
)

from log import logger

from ..default import DefaultDjangoTgORM

from reaiogram.types import MergedTelegramDocument

# from asgiref.sync import sync_to_async, async_to_sync


class DjangoORMTgFile(
    DefaultDjangoTgORM
):

    async def select_tg_file_id(
            self, file_id: str,
            db_class: Union[
                type(DjangoTgDocument),
            ]
    ):

        data = DjangoTgDocument()

        self.set_select(
            data=data,
            select_kwargs={
                'file_id': file_id,
            },
            set_keys=True,
        )
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

        self.set_select(
            data=data,
            select_kwargs={
                'file_id': data.file_id
            }
        )
        return await self.update_one(
            data=data, db_class=db_class,
        )
