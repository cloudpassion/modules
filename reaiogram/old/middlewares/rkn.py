from aiogram import types
from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from log import flogger


class RKN(BaseMiddleware):

    async def on_pre_process_update(self, update: types.Update, data: dict):
        flogger.info(f'----------------------------------------RNK\n'
                  f'{data}'
                  f'----------------------------------------')

        data["middleware_data"] = 'test1'


    async def on_process_update(self, update: types.Update, data: dict):
        flogger.info(f'----RKN2\n'
                  f'{data}\n'
                  f'--------')

    async def on_pre_process_message(self, m: types.Message, data: dict):
        flogger.info(f'prcm: {data}')
        data["middleware_data"] = 'test3'

    # filters

    async def on_process_message(self, m: types.Message, data: dict):
        data["test_data"] = 'check this out'


def register_rkn_middleware(dp):
    return
    #dp.middleware.setup(RKN())
