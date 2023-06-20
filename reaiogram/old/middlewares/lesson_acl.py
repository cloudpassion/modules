from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware


from reaiogram.db.schemas.lesson.models import LessonChatModel


class LessonACLMiddleware(BaseMiddleware):

    async def setup_chat(self, data: dict, chat: types.Chat):

        chat_id = chat.id

        chat = LessonChatModel.get_or_create(chat_id)
        data["chat"] = chat

    async def on_pre_process_message(self, m: types.Message, data: dict):
        await self.setup_chat(data, m.chat)


def register_lesson_acl_middleware(dp):
    dp.middleware.setup(LessonACLMiddleware())
