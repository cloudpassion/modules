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

        await self._default_merge_telegram('init_bot')

        return self
        # await self._convert_to_orm()

    async def to_orm(self):
        return await self.db.update_tg_bot(
            bot=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_bot(
            id=self.id
        )
