from aiogram import types
from aiogram.contrib.middlewares.logging import LoggingMiddleware as DefaultLoggingMiddleWare

from log import flogger


class LoggingMiddleware(DefaultLoggingMiddleWare):

    def __init__(self, logger=__name__):
        self.logger = logger
        super(LoggingMiddleware, self).__init__(logger)

        from config import settings

        try:
            self.timeline = settings.log.middleware.timeline
        except AttributeError:
            self.timeline = False

        try:
            self.kafka = settings.log.middleware.kafka
        except AttributeError:
            self.kafka = False

    async def on_pre_process_update(self, update: types.Update, data: dict):
        await super(LoggingMiddleware, self).on_pre_process_update(update, data)

        if self.kafka:
            self.logger.warning({'update': update.as_json(), 'data': f"{data}"})

        if self.timeline:
            pass


def register_logging_middleware(dp):
    dp.middleware.setup(LoggingMiddleware(logger=flogger))
