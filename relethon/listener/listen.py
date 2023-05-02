import telethon.events.common
from telethon import events, TelegramClient
from collections import defaultdict

from config import settings, secrets
from log import logger, log_stack

from ..client.default import MyAbstractTelegramClient


class MyTelethonListener(
    MyAbstractTelegramClient, TelegramClient
):

    async def incoming_forward(self):
        settings_forward = settings.forward.enable
        if not settings_forward:
            return

        settings_forward_blacklist = secrets.forward.blacklist
        settings_forward_from = secrets.forward.source
        settings_forward_to = secrets.forward.forward_to

        if isinstance(settings_forward_from, list):
            from_chats = settings_forward_from
        else:
            from_chats = None

        if isinstance(settings_forward_to, list):
            for from_to in settings_forward_to:
                self.forward_from_to[from_to[0]] = from_to[1]
        else:
            self.forward_from_to = defaultdict(lambda: settings_forward_to, {})

        @self.on(events.NewMessage(
            chats=from_chats, blacklist_chats=settings_forward_blacklist
        ))
        @self.on(events.MessageEdited(
            chats=from_chats, blacklist_chats=settings_forward_blacklist
        ))
        @self.on(events.MessageDeleted(
            chats=from_chats, blacklist_chats=settings_forward_blacklist
        ))
        async def _forward(event):

            try:
                if settings.forward.log:
                    logger.info(f'{event=}')

                    logger.info(f'ev.chat_id: {event.chat_id}')
                    logger.info(f'event.type: {type(event)}')
                    logger.info(f'dir: {dir(event)}')
                    logger.info(f'ev.chat: {event.chat}')
                    try:
                        logger.info(f'ev.msg: {event.message}')
                    except:
                        pass

                    logger.info(f'ev.or_update: {event.original_update}')

                if hasattr(event, 'out') and event.out:
                    if settings.forward.log:
                        logger.info(f'outgoing')
                    return

                try:
                    from_chat_id = event.chat.id
                except:
                    try:
                        from_chat_id = event.original_update.channel_id
                    except:
                        from_chat_id = event.chat_id

                if from_chat_id in secrets.forward.skip:
                    if settings.forward.log:
                        logger.info(f'chat skip 1')
                    return

                if event.chat_id in secrets.forward.skip:
                    if settings.forward.log:
                        logger.info(f'chat skip 2')
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
                )
                try:
                    await event.forward_to(to_chat_id)
                except:
                    pass
            except:
                log_stack.error('stack')

    async def new_messages_handler(self):
        @self.on(events.NewMessage())
        async def _new_message_handler(event):

            if settings.forward.log:
                logger.info(f'{event=}')

                logger.info(f'ev.chat_id: {event.chat_id}')
                logger.info(f'event.type: {type(event)}')
                logger.info(f'dir: {dir(event)}')
                logger.info(f'ev.chat: {event.chat}')
                logger.info(f'ev.msg: {event.message}')
                logger.info(f'ev.or_update: {event.original_update}')

            # try:
            #     local_cmd, merge_chat = await main_cmd.check_chat(
            #         event_data=event, tg=self, conf=self.conf
            #     )
            #     #tasks = (
            #     #    asyncio.create_task(local_cmd.check(None, None, merge_chat=merge_chat)),
            #     #)
            #     #results = await asyncio.gather(*tasks)
            #     ret = await local_cmd.check(None, None, merge_chat=merge_chat)
            #     #logger.info(f'ret: {ret}')
            # except:
            #     log_stack.info(f'event: {event}')
