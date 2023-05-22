import asyncio
import random
import re
import pyrogram
import string
import itertools
import ujson as json

from datetime import datetime
from pyrogram.errors.exceptions.flood_420 import FloodWait
from collections import deque

from pyrogram.raw.functions.messages import SendMedia
from pyrogram.raw.types import (
    InputPeerChat, InputBotInlineMessageMediaContact,
    InputMediaContact, Contact
)

# from pyrogram.raw.base import (
#     Contact,
# )

from pyrogram.raw.functions.contacts import AddContact, ResolvePhone
from pyrogram import Client as PyrogramClient
from pyrogram.types import (
    Message as PyrogramMessage, InputPhoneContact,
)

from ..client import MyAbstractTelegramClient
from ..db.types.message import MyEventMessageDatabase

from config import settings
from log import logger, log_stack


class MyPyroTestFunc(
    MyAbstractTelegramClient,
    PyrogramClient
):

    async def send_new_contact(self):

        phone = '+71'
        chat_id = 1

        contact = InputPhoneContact(
            phone, first_name='d',
        )

        # med = InputMediaContact(
        #     phone_number=phone, first_name='d',
        # )
        med = Contact(user_id=1, mutual=False)
        logger.info(f'{med=}')
        await self.invoke(
            SendMedia(
                peer=chat_id,
                media=med,
                reply_to_msg_id=1140,
                random_id=random.randint(1, 10000),
                message='',
            )
        )
        # await self.send_contact(
        #     chat_id, phone_number=phone, first_name='d',
        #     reply_to_message_id=1140,
        # )




