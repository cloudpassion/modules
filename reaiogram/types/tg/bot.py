from log import logger

from .merged.aiogram.types import AiogramUser
from .merged.aiogram.bot import MergedAiogramBot

from ...types.django import (
    TgBot,
)


class MergedTelegramBot(
    # MergedPyrogramMessage,
    MergedAiogramBot,
):

    def __init__(self, orm, bot):
        self.orm = orm
        self.unmerged = bot

    async def merge_bot(self):

        if self.unmerged is None:
            # logger.info(f'no bot {hex(id(self))=}')
            return None

        await self._default_merge_telegram('init_bot')

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramUser,
        )):
            await self._merge_aiogram_bot()

        await self._convert_to_orm()
        return self
