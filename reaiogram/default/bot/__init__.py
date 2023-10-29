from typing import Optional

from ..aiohttp.session import AiohttpSession

from .me_orm import OrmMeBot
from .resession import ReBaseSession
from .requests import RequestsHandlerBot
from .wait import WaitLimitBot


class Bot(
    OrmMeBot,
    RequestsHandlerBot,
    WaitLimitBot,
):

    def __init__(
            self,
            token: str,
            session: Optional[ReBaseSession] = None,
            parse_mode: Optional[str] = None,
            disable_web_page_preview: Optional[bool] = None,
            protect_content: Optional[bool] = None,
    ) -> None:
        super().__init__(
            token=token,
            session=AiohttpSession(),
            # session=session,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            protect_content=protect_content
        )
        # self.session = ReBaseSession