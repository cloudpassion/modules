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

from .merged.aiogram.types import AiogramChat
from .merged.aiogram.chat import MergedAiogramChat

from ...types.django import (
    TgChat,
)

# from .chats import MyChatDatabase
# from .media import MyTelegramParseMedia
# from .reactions import MyTelegramReactions


class MergedTelegramChat(
    # MergedPyrogramMessage,
    MergedAiogramChat,
):

    def __init__(self, db, chat=None):
        self.unmerged = chat
        self.db_class = TgChat
        self.db = db

    async def merge_chat(self):
        # if isinstance(self.init_message, (
        #     PyrogramMessage,
        # )):
        #     return await self._merge_pyrogram_message()

        if isinstance(self.unmerged, (
                AiogramChat,
        )):
            return await self._merge_aiogram_chat()
