# import asyncio
# import hashlib
# import pyrogram.enums
# import pyrogram.types

# import ujson as json

# from collections import deque
# from typing import Union, List
# from datetime import datetime
# from asgiref.sync import sync_to_async, async_to_sync

# from pyrogram.raw.functions.messages import GetReplies
# from pyrogram.errors.exceptions.flood_420 import FloodWait

# from .pyrogram.types import PyrogramMessage
# from .pyrogram.message import MergedPyrogramMessage

from log import logger

from .merged.aiogram.types import AiogramMessage
from .merged.aiogram.message import MergedAiogramMessage

from ...types.django import (
    TgMessage,
)

# from .chats import MyChatDatabase
# from .media import MyTelegramParseMedia
# from .reactions import MyTelegramReactions


class MergedTelegramMessage(
    # MergedPyrogramMessage,
    MergedAiogramMessage,
):

    def __init__(self, orm, message):

        self.orm = orm
        self.unmerged = message

    async def merge_message(self):

        if self.unmerged is None:
            # logger.info(f'no message {hex(id(self))=}')
            return None

        await self._default_merge_telegram('m_a_message')

        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
            AiogramMessage,
        )):
            await self._merge_aiogram_message()

        await self._convert_to_orm()
        return self
