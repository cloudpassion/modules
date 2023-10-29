import re

from log import logger

from .default import DefaultBot


class WaitLimitBot(DefaultBot):

    async def send_document(
            self,
            *args,
            **kwargs,
    ):
        async with self.dp.upload_sem:
            return await super().send_document(*args, **kwargs)

