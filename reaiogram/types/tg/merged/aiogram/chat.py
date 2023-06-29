from .types import AiogramChat

from reaiogram.types.tg.merged.default.chat import AbstractMergedChat


class MergedAiogramChat(
    AbstractMergedChat,
):

    unmerged: AiogramChat

    async def _merge_aiogram_chat(self):
        # if not self.unmerged:
        #     return

        return self

    async def to_orm(self):

        await self.orm.add_tg_chat_history(
            chat=self
        )

        return await self.orm.update_tg_chat(
            chat=self,
        )

    async def from_orm(self):
        return await self.orm.select_tg_chat_id(
            id=self.id
        )
