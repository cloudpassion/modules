
from telethon.client import (
    AccountMethods, AuthMethods, DownloadMethods, DialogMethods, ChatMethods,
    BotMethods, MessageMethods, UploadMethods, ButtonMethods, UpdateMethods,
    MessageParseMethods, UserMethods, TelegramBaseClient
)
from telethon import TelegramClient

from config import settings, secrets
from log import logger, log_stack

from ..listener import MyTelethonListener


class MyTelegramClient(
    MyTelethonListener, TelegramClient
):

    def __init__(self):

        # auth
        _session_name = secrets.telethon.session_name
        _api_id = secrets.telethon.api_id
        _api_hash = secrets.telethon.api_hash

        # config

        super(MyTelegramClient, self).__init__(
            session=_session_name,
            # api get from https://my.telegram.org
            api_id=_api_id,
            api_hash=_api_hash,
            request_retries=10,
            retry_delay=60,
            auto_reconnect=True,
            connection_retries=60,
        )

        # misc
        self.timezone_offset = settings.misc.timezone_offset
        self.timezone_name = settings.misc.timezone_name

    async def client_start(self):

        await self.start()
        await self.run_until_disconnected()
