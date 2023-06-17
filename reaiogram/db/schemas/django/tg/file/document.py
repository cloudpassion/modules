from .default import DjangoORMTgFile

from typing import Union

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgDocument as DjangoTgDocument
)

from log import log_stack, logger


from ......db.types import MergedAiogramDocument, MergedTelegramDocument

# from asgiref.sync import sync_to_async, async_to_sync


class DjangoORMTgDocument(
    DjangoORMTgFile
):

    async def select_tg_document_file_unique_id(
            self, file_unique_id: str,
    ):

        return await self.select_tg_file_unique_id(
            file_unique_id, db_class=DjangoTgDocument
        )

    async def update_tg_document(
            self, document: MergedTelegramDocument,
    ) -> DjangoTgDocument:

        return await self.update_tg_file(
            data=document, db_class=DjangoTgDocument
        )
