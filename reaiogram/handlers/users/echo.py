from aiogram.types import Message
from reaiogram.dispatcher.default import Dispatcher


# how to register first variant
class EchoHandler(Dispatcher):

    # func always starts with _append_handler_
    # this func loads from Dispatcher on init
    async def _append_handler_echo_bot(self):

        @self.message_handler(commands=["echo_dec"])
        async def some_func(m: Message):
            await m.reply(f"echo dec")


# how to register second variant
async def handler_echo(m: Message):
    await m.reply(f"echo reg")


def register_echo(dp: EchoHandler):
    dp.register_message_handler(handler_echo, commands=["echo_reg"])
