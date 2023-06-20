from .merged.aiogram.types import AiogramUser
from .merged.aiogram.bot import MergedAiogramBot

from ...types.django import (
    TgBot,
)


class MergedTelegramBot(
    # MergedPyrogramMessage,
    MergedAiogramBot,
):

    def __init__(self, db, bot=None):
        self.unmerged = bot
        self.db_class = TgBot
        self.db = db

    async def merge_bot(self):
        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUser,
        )):
            return await self._merge_aiogram_bot()
