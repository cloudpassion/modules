from aiogram.dispatcher.filters import Regexp
from aiogram.utils import exceptions
from aiogram import types
from aiogram.types.chat_member import ChatMemberStatus

from reaiogram.dispatcher.default import Dispatcher
from log import mlog, log_stack


class LessonInlineHandler(Dispatcher):

    async def _append_handler_lesson_inline(self):

        @self.inline_handler(Regexp('([a-zа-я0-9]){3,100}'))
        async def lesson_inline_handler(query: types.InlineQuery):
            await query.answer(
                results=[
                    types.InlineQueryResultArticle(
                        id="unknow",
                        title="Vvedite zapros",
                        input_message_content=types.InputMessageContent(
                            message_text="Ne obyzatelno",
                        )
                    )
                ], cache_time=5
            )

