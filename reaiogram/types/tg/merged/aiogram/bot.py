from .types import AiogramUser

from reaiogram.types.tg.merged.default.bot import AbstractMergedBot


class MergedAiogramBot(
    AbstractMergedBot,
):

    unmerged: AiogramUser

    async def _merge_aiogram_bot(self):
        #
        # if not self.unmerged:
        #     return

        return self
        # await self._convert_to_orm()

    async def to_orm(self):
        return await self.orm.update_tg_bot(
            bot=self,
        )

    async def from_orm(self):
        return await self.orm.select_tg_bot(
            id=self.id
        )
