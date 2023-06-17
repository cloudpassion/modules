import typing

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from log import flogger


class PostQueryAnswer(BaseMiddleware):

    async def on_post_process_callback_query(
            self, c: typing.Union[types.CallbackQuery,
                                  types.InlineQuery], *args
                                             ):
        flogger.info(f'------ answer on query: {c.__class__.__name__}')
        await c.answer()


def register_pqa_middleware(dp):
    dp.middleware.setup(PostQueryAnswer())
