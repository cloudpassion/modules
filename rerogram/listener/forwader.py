from pyrogram import Client as PyrogramClient
from collections import defaultdict

from atiny.datime.date import dt_parse
from config import settings
from log import logger, log_stack

from ..client import MyAbstractTelegramClient


class MyPyrogramForwarder(MyAbstractTelegramClient, PyrogramClient):

    async def incoming_forward(self):
        settings_forward = settings.forward.enable
        if not settings_forward:
            return

        settings_forward_blacklist = settings.forward.blacklist
        settings_forward_from = settings.forward.source
        settings_forward_to = settings.forward.forward_to
        settings_forward_skip = settings.forwars.skip

        if isinstance(settings_forward_from, list):
            from_chats = settings_forward_from
        else:
            from_chats = None

        if isinstance(settings_forward_to, list):
            for from_to in settings_forward_to:
                self.forward_from_to[from_to[0]] = from_to[1]
        else:
            self.forward_from_to = defaultdict(lambda: settings_forward_to, {})

        @self.on_message(
        #     events.NewMessage(
        #     chats=from_chats, blacklist_chats=settings_forward_blacklist
        # )
        )
        @self.on_edited_message(
        #     events.MessageEdited(
        #     chats=from_chats, blacklist_chats=settings_forward_blacklist
        # )
        )
        @self.on_deleted_messages(
        #     events.MessageDeleted(
        #     chats=from_chats, blacklist_chats=settings_forward_blacklist
        # )
        )
        async def _forward(event):

            try:
                logger.info(f'{event=}')

                logger.info(f'event.type: {type(event)}')
                logger.info(f'dir: {dir(event)}')
                logger.info(f'ev.chat: {event.chat}')
                try:
                    logger.info(f'ev.msg: {event.message}')
                except:
                    pass

                logger.info(f'ev.or_update: {event.original_update}')

                try:
                    from_chat_id = event.chat.id
                except:
                    try:
                        from_chat_id = event.original_update.channel_id
                    except:
                        from_chat_id = event.chat_id

                if from_chat_id in settings_forward_skip:
                    logger.info(f'skip chat')
                    return

                to_chat_id = self.forward_from_to[from_chat_id]

                message_links = []
                try:
                    message_links.append(
                        f'https://t.me/c/{from_chat_id}/{event.message.id}'
                    )
                except:
                    for msg_id in event.original_update.messages:
                        message_links.append(
                            f'https://t.me/c/{from_chat_id}/{msg_id}'
                        )

                try:
                    chat_title = event.chat.title
                except:
                    chat_title = 'no title'

                message = f'From ' \
                          f'{from_chat_id}, {chat_title}\n' \
                          f'{event=}\n' \
                          f'{", ".join(message_links)}'

                await self.send_message(
                    to_chat_id,
                    message,
                    disable_notification=True,
                )
                try:
                    await event.forward_to(
                        to_chat_id,
                        silent=True,
                    )
                except:
                    pass
            except:
                log_stack.error('stack')
