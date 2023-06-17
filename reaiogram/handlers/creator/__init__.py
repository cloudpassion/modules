from aiogram.dispatcher import filters
from aiogram import types

from reaiogram.dispatcher.default import Dispatcher
from reaiogram.menus import creator_markup
from reaiogram.commands import creator_commands
from reaiogram.filters import CreatorFilter


class BotCreatorHandler(Dispatcher):

    async def _append_handler__bot_creator(self):

        @self.message_handler(
            filters.ChatTypeFilter(chat_type=types.ChatType.PRIVATE),
            creator_commands,
            CreatorFilter()
        )
        async def is_creator(m: types.Message):
            # you creator from config
            # no answer if no creator send this commands
            await m.reply(
                "You are creator of this bot",
                reply_markup=creator_markup(),
            )
