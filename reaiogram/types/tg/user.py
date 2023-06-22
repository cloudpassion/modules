# import pyrogram.enums
# import pyrogram.types

# from pyrogram.raw.functions.messages import GetReplies
# from pyrogram.errors.exceptions.flood_420 import FloodWait

from log import logger


from .merged.aiogram.types import AiogramUser
from .merged.aiogram.user import MergedAiogramUser

from ...types.django import TgUser


class MergedTelegramUser(
    MergedAiogramUser,
):

    def __init__(self, db, user):
        self.unmerged = user
        self.db_class = TgUser
        self.db = db

    async def merge_user(self):

        if self.unmerged is None:
            # logger.info(f'no user {hex(id(self))=}')
            return None

        # if isinstance(self.init_message, (
        #         PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUser,
        )):
            await self._merge_aiogram_user()

        await self._convert_to_orm()
        return self
