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

from config import settings
from log import logger, log_stack

# from .pyrogram.types import PyrogramMessage
# from .pyrogram.message import MergedPyrogramMessage

from .aiogram.types import AiogramMessage
from .aiogram.message import MergedAiogramMessage

from ..types.django import (
    TgMessage,
)

# from .chats import MyChatDatabase
# from .media import MyTelegramParseMedia
# from .reactions import MyTelegramReactions


class MergedTelegramMessage(
    # MergedPyrogramMessage,
    MergedAiogramMessage,
):

    def __init__(self, db, message=None):
        self.unmerged = message
        self.db_class = TgMessage
        self.db = db

    async def merge_message(self):
        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
            AiogramMessage,
        )):
            return await self._merge_aiogram_message()
