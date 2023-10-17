from typing import Any, Optional, Type, Dict, AsyncGenerator

from aiogram import exceptions

from aiohttp import ClientSession, TCPConnector
from aiohttp.hdrs import USER_AGENT
from aiohttp.http import SERVER_SOFTWARE
from aiogram.__meta__ import __version__

from aiogram.client.session.aiohttp import (
    AiohttpSession as DefaultAiohttpSession,
    TelegramType,
)

from log import logger, log_stack


class AiohttpSession(DefaultAiohttpSession):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._connector_init: Dict[str, Any] = {
            **self._connector_init,
            'limit': 25,
            'enable_cleanup_closed': True,
            'force_close': True,
        }

    async def make_request(
            self, *args, **kwargs,
    ) -> TelegramType:
        # try:
        if True:
            return await super().make_request(*args, **kwargs)
        # except Exception as exc:
        #     logger.info(f'sq: {exc=}'[:512])
        #     raise
        #     # raise Exception from exc
        #     # log_stack.error(f's1: {exc=}')

    # async def create_session(self) -> ClientSession:
    #
    #     _session: ClientSession = await super().create_session()
    #
    #     logger.info(f'{_session.connector=}')
    #     return _session
    #
    #     if self._should_reset_connector:
    #         await self.close()
    #
    #     if self._session is None or self._session.closed:
    #         self._session = ClientSession(
    #             connector=self._connector_type(**self._connector_init),
    #             headers={
    #                 USER_AGENT: f"{SERVER_SOFTWARE} aiogram/{__version__}",
    #             },
    #         )
    #         self._should_reset_connector = False
    #
    #     return self._session
    # async def stream_content(
    #         self, url: str, timeout: int, chunk_size: int, raise_for_status: bool
    # ) -> AsyncGenerator[bytes, None]:
    #     session = await self.create_session()
    #
    #     async with session.get(url, timeout=timeout, raise_for_status=raise_for_status) as resp:
    #         async for chunk in resp.content.iter_chunked(chunk_size):
    #             yield chunk
