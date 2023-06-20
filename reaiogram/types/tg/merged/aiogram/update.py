from log import logger


from .types import AiogramUpdate

from ...merged.default.update import AbstractMergedUpdate

from ...message import MergedTelegramMessage


class MergedAiogramUpdate(
    AbstractMergedUpdate,
):

    unmerged: AiogramUpdate

    async def _merge_aiogram_update(self):

        # logger.info(f'{self.unmerged=}')
        await self._default_merge_telegram()

        self.bot = self.merged_bot

        # update_id
        self.id = self.unmerged.update_id

        for upd in (
            'message', 'edited_message',
            'channel_post', 'edited_channel_post',
        ):
            merged = MergedTelegramMessage(
                db=self.db,
                message=getattr(
                    self.unmerged,
                    upd,
                ),
            )

            setattr(
                self, upd, merged
            )
            self_merged = getattr(self, upd)
            await self_merged._merge_aiogram_message()

    async def to_orm(self):
        return await self.db.update_tg_update(
            update=self,
        )

    async def from_orm(self):
        return await self.db.select_tg_update(
            bot=self.bot, id=self.id
        )
