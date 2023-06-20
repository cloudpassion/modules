from .types import AiogramUser

from reaiogram.types.tg.merged.default.bot import AbstractMergedBot


class MergedAiogramBot(
    AbstractMergedBot,
):

    unmerged: AiogramUser

    async def _merge_aiogram_bot(self):
        await self._default_merge_telegram()

    async def to_orm(self):
        return await self.db.update_tg_bot(
            bot=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_bot(
            id=self.id
        )
