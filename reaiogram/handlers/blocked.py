from aiogram.utils import exceptions
from aiogram import types
from aiogram.types.chat_member import ChatMemberStatus

from reaiogram.dispatcher.default import Dispatcher
from log import mlog, log_stack


class BlockedHandler(Dispatcher):

    async def _append_handler_blocked(self):

        @self.errors_handler(exception=exceptions.BotBlocked)
        async def bot_blocked(update: types.Update, exception: exceptions.BotBlocked):
            log_stack.info(
                f'Bot blocked by user {update.message.from_user.id}: {update.message.date}'
            )
            return True

        @self.my_chat_member_handler()
        async def bot_kicked(update: types.ChatMemberUpdated):
            if update.new_chat_member.status == ChatMemberStatus.KICKED:
                mlog.info(
                    f'Bot kicked by user {update.from_user.id}: {update.date}\n'
                )
            elif update.new_chat_member.status == ChatMemberStatus.MEMBER:
                mlog.info(
                    f'User return Bot from hell {update.from_user.id}: {update.date}\n'
                )
            return True
