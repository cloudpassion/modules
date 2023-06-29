from log import logger

from aiogram.enums.update_type import UpdateType

from .....utils.enums import MESSAGE_UPDATE_TYPES
from ...merged.default.update import AbstractMergedUpdate
from ...message import MergedTelegramMessage
from .types import AiogramUpdate


class MergedAiogramUpdate(
    AbstractMergedUpdate,
):

    unmerged: AiogramUpdate

    async def _merge_aiogram_update(self):
        #
        # if not self.unmerged:
        #     return

        # update_id
        self.id = self.unmerged.update_id

        classess_to_merge = {
            **{
                k: MergedTelegramMessage for k in MESSAGE_UPDATE_TYPES
            }
        }
        func_name_to_merge = {
            **{
                k: 'merge_message' for k in MESSAGE_UPDATE_TYPES
            }
        }
        key_to_merge = {
            **{
                k: 'message' for k in MESSAGE_UPDATE_TYPES
            }
        }
        # logger.info(f'{classess_to_merge}')

        for upd_key in UpdateType:
            if upd_key not in classess_to_merge:
                # logger.info(f'skip_parsing: {upd_key=}')
                continue

            unmerged = getattr(self.unmerged, upd_key)
            if not unmerged:
                continue

            merge_class = classess_to_merge[upd_key]
            merge_kwargs = {key_to_merge.get(upd_key): unmerged}
            merged = merge_class(
                orm=self.orm,
                **merge_kwargs,
            )

            merge_func = getattr(merged, func_name_to_merge[upd_key])
            await merge_func()

            setattr(
                self, upd_key, merged
            )

        return self

    async def to_orm(self):
        return await self.orm.update_tg_update(
            update=self,
        )

    async def from_orm(self):
        return await self.orm.select_tg_update(
            bot=self.bot, id=self.id
        )
