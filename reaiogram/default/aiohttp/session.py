from typing import Any, Optional, Type, Dict, AsyncGenerator

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
        }

    async def make_request(
            self, *args, **kwargs,
    ) -> TelegramType:
        try:
            return await super().make_request(*args, **kwargs)
        except Exception as exc:
            log_stack.error('s1')

    async def stream_content(
            self, url: str, timeout: int, chunk_size: int, raise_for_status: bool
    ) -> AsyncGenerator[bytes, None]:
        session = await self.create_session()

        async with session.get(url, timeout=timeout, raise_for_status=raise_for_status) as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk
