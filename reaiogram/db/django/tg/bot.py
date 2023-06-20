from typing import Union

from ....django_telegram.django_telegram.datamanager.models import (
    TgBot as DjangoTgBot,
)

from .default import DefaultDjangoTgORM

from reaiogram.types import MergedAiogramBot, MergedTelegramBot


class DjangoORMTgBot(
    DefaultDjangoTgORM
):
    async def select_tg_bot(self, id: int) -> DjangoTgBot:

        bot = DjangoTgBot()
        self.set_select(
            data=bot,
            select_kwargs={'id': id},
            set_keys=True,
        )
        return await self.select_one(
            data=bot, db_class=DjangoTgBot
        )

    async def update_tg_bot(
            self, bot: Union[
                MergedAiogramBot,
                MergedTelegramBot,
            ],
    ):
        return await self.update_one(
            data=bot, db_class=DjangoTgBot
        )
