# import pyrogram.enums
# import pyrogram.types

# from pyrogram.raw.functions.messages import GetReplies
# from pyrogram.errors.exceptions.flood_420 import FloodWait

from log import logger


from .merged.aiogram.types import AiogramUser
from .merged.aiogram.user import MergedAiogramUser


class MergedTelegramUser(
    MergedAiogramUser,
):

    def __init__(self, orm, user, skip_orm=False):

        self.orm = orm
        self.unmerged = user
        self.skip_orm = skip_orm

    async def merge_user(self):

        if self.unmerged is None:
            # logger.info(f'no user {hex(id(self))=}')
            return None

        await self._default_merge_telegram('m_a_user')

        # if isinstance(self.init_message, (
        #         PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUser,
        )):
            await self._merge_aiogram_user()

        if not self.skip_orm:
            await self._convert_to_orm()

        return self
