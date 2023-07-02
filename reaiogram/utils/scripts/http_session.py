from aiogram.client.telegram import TelegramAPIServer

from ...default.aiohttp.session import AiohttpSession
from ...loader.setup import (
    API_BASE_URL, API_FILE_URL,
)


def create_http_session():
    api_session = AiohttpSession(
        # proxy=f'http://{secrets.proxy.http.ip}:{secrets.proxy.http.port}',
        proxy=None,
        api=TelegramAPIServer(
            base=API_BASE_URL,
            file=API_FILE_URL,
        ),
    )

    return api_session
