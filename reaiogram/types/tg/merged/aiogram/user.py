from .types import AiogramUser

# from ....db.schemas.django.tg.user import DjangoORMTgUser
#
from reaiogram.types.tg.merged.default.user import AbstractMergedUser


class MergedAiogramUser(
    AbstractMergedUser,
):

    unmerged: AiogramUser

    async def _merge_aiogram_user(self):
        await self._default_merge_telegram()

    async def to_orm(self):

        await self.db.add_tg_user_history(
            user=self
        )
        return await self.db.update_tg_user(
            user=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_user_id(
            id=self.id
        )
