from aiogram import types
from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from log import logger


class Task5M(BaseMiddleware):

    async def on_pre_process_message(self, msg: types.Message, data: dict):
        logger.info(f'prcm: {data}')
        data["middleware_data"] = 'test3'

    # filters

    #
    async def on_process_message(self, msg: types.Message, data: dict):
        data["test_data"] = 'check this out'


def register_task5_middleware(dp):
    return
    dp.middleware.setup(Task5M())
