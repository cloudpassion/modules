from typing import Union

from reaiogram.django_telegram.django_telegram.datamanager.models import (
    TgUser as DjangoTgUser,
    TgUserHistory as DjangoTgUserHistory,
)

from log import log_stack, logger

from reaiogram.db.schemas.django.tg.default import DefaultDjangoORM

# from reaiogram.django_telegram.django_telegram.datamanager.tg.user import USER_KEYS

from .....db.types.user import MergedAiogramUser, MergedTelegramUser


class DjangoORMTgUser(
    DefaultDjangoORM
):

    async def select_tg_user_id(self, id: int) -> DjangoTgUser:

        user = DjangoTgUser()
        self.set_select(
            data=user,
            select_kwargs={'id': id},
            set_keys=True

        )
        logger.info(f'here32')
        return await self.select_one(
            data=user, db_class=DjangoTgUser
        )

    # async def add_tg_user(
    #         self,
    #         user: MergedAiogramUser,
    # ) -> DjangoTgUser:
    #
    #     logger.info(f'here32')
    #     return await self.add_one(
    #         data=user, db_class=DjangoTgUser
    #     )
    async def add_tg_user_history(
            self, user: Union[
                MergedTelegramUser
            ],
    ):

        return await self.add_one_history(
            data=user, db_class=DjangoTgUserHistory
        )

    async def update_tg_user(
            self, user: Union[
                MergedTelegramUser
            ],
    ):

        return await self.update_one(
            data=user, db_class=DjangoTgUser
        )
