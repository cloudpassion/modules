from typing import Union

from log import logger

from ....django_telegram.django_telegram.datamanager.models import (
    TgUpdate as DjangoTgUpdate,
)

from .default import DefaultDjangoTgORM

from reaiogram.types import MergedTelegramBot
from reaiogram.types import MergedAiogramUpdate


class DjangoORMTgUpdate(
    DefaultDjangoTgORM
):

    async def select_tg_last_update(
            self, bot: MergedTelegramBot
    ):

        logger.info(f'start_get_last_update')
        update = DjangoTgUpdate()
        self.set_select(
            data=update,
            select_kwargs={
                'bot': await self.select_tg_bot(id=bot.id),
            },
            set_keys=True,
        )
        last_update = await self.select_max(
            data=update, db_class=DjangoTgUpdate
        )
        logger.info(f'end_get_last_update')

        return last_update

    async def select_tg_update(
            self, bot: MergedTelegramBot, id: int
    ):

        update = DjangoTgUpdate()

        self.set_select(
            data=update,
            select_kwargs={
                'bot': bot,
                'id': id,
            },
            set_keys=True,
        )
        return await self.select_one(
            data=update, db_class=DjangoTgUpdate
        )

    async def update_tg_update(
            self,
            update: Union[
                MergedAiogramUpdate
            ],
    ) -> DjangoTgUpdate:

        bot = await self.select_tg_bot(
            id=update.bot.id
        )

        self.set_select(
            data=update,
            select_kwargs={
                'bot': bot,
                'id': update.id,
            }
        )
        return await self.update_one(
            data=update, db_class=DjangoTgUpdate
        )

