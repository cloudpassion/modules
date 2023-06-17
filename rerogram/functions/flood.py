import asyncio
import re
import pyrogram
import string
import itertools
import ujson as json

from pyrogram.errors.exceptions.flood_420 import FloodWait
from collections import deque

from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage

from ..client import MyAbstractTelegramClient
from ..db.types.message import MyEventMessageDatabase

from config import settings
from log import logger, log_stack

FLOOD_WAIT_X = {
    'messages.SendMessage': 0
}


class MyPyrogramFlood(
    MyAbstractTelegramClient,
    PyrogramClient
):

    async def parse_flood(self, where, exc, wait=True):
        logger.info(f'{where=}, {exc=}')

        flood = re.search(f'FLOOD_WAIT_X', f'{exc}')
        if flood:
            reason = re.findall('"(.*?)"', f'{exc}')[0]
            count = re.findall('A wait of (.*?) seconds', f'{exc}')[0]
            if count:
                count = int(count)
            else:
                count = 0
            FLOOD_WAIT_X[reason] = count
            if not wait:
                return

            while count > 0:
                logger.info(f'sleep {count=}')
                await asyncio.sleep(10)
                count -= 10
