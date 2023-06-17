from aiogram import types
from aiogram.utils import exceptions
from aiogram.dispatcher.middlewares import BaseMiddleware

from config import secrets


class ForwarderMiddleware(BaseMiddleware):

    async def on_pre_process_update(self, u: types.Update, *args):
        if not secrets.aiogram.forward:
            return

        await u.bot.send_message(secrets.aiogram.forward, text=f'{u.as_json()}')

    # TODO: parse update as its type of message forward it object


def register_forwarder_middleware(dp):
    dp.middleware.setup(ForwarderMiddleware())
