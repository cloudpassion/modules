# import pyrogram.enums
# import pyrogram.types

# from pyrogram.raw.functions.messages import GetReplies
# from pyrogram.errors.exceptions.flood_420 import FloodWait

from .aiogram.types import AiogramUser
from .aiogram.user import MergedAiogramUser

from ..types.django import TgUser


class MergedTelegramUser(
    MergedAiogramUser,
):

    def __init__(self, db, user=None):
        self.unmerged = user
        self.db_class = TgUser
        self.db = db

    async def merge_user(self):
        # if isinstance(self.init_message, (
        #         PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUser,
        )):
            return await self._merge_aiogram_user()
