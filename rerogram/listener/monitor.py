import asyncio
import re

import pyrogram.raw.types
from pyrogram import Client as PyrogramClient
from collections import defaultdict

from atiny.datime.date import dt_parse
from config import settings
from log import logger, log_stack

from .discussion import MyTelethonChannelDiscussion
from .discussion_forward import MyTelethonChannelDiscussionForward
from ..db.types import MyTelethonEventsDatabase


class MyPyrogramMonitor(
    MyTelethonEventsDatabase,
    MyTelethonChannelDiscussion,
    MyTelethonChannelDiscussionForward,
    PyrogramClient,
):

    async def events(self):

        @self.on_message()
        async def new_message_event(client, event):
            # log, session
            if settings.log.log_session:
                self.log_event(event)
            if settings.log.save_session:
                self.save_event(event)

            if settings.log.help:
                self.log_event(event, force=True)

            # event to database
            if settings.database.new_message:
                async def wait_db():
                    _done, pending = await asyncio.wait(
                        [self.database_message(event, delete=False), ],
                        return_when=asyncio.ALL_COMPLETED,
                    )

                    logger.info(f'was1: {pending=}, {_done=}')
                    while pending:
                        await asyncio.sleep(0.1)
                        logger.info(f'was2: {pending=}, {_done=}')

                    return _done

                # done = await wait_db()
                # db = list(done)[0].result()

                db = await self.database_message(event, delete=False)

                # while True:
                #
                #     logger.info(f'wait: {event.id=}, {db=}')
                #     if re.search(f'{db}'.lower(), 'skip|return|true'):
                #         break
                #
                #     if re.search(f'{db}'.lower(), 'stack'):
                #         done = await wait_db()
                #         db = list(done)[0].result()
                #         await asyncio.sleep(0.1)
                #         continue
                #
                #     db_check = self.db.select(
                #         'message',
                #         event.chat.id,
                #         id=event.id,
                #     )
                #     if db_check:
                #         break
                #
                #     logger.info(f'{db=}, {db_check=}')
                #     await asyncio.sleep(0.1)

                if db is True and settings.database.none_quit:
                    if settings.log.database.none_quit and hasattr(
                            event, 'db_quit'
                    ):
                        logger.info(f'db_quit: {event.db_quit}')
                    return

            # discussion
            if settings.discussion.enable:
                await self.discuss_new_message(event)

            # discussion forward
            if settings.discussion.forward.enable:
                if event.chat.id in self.discussion_fwd_data:
                    await self.discuss_forward_new(
                        event=event,
                        data=self.discussion_fwd_data[event.chat.id]
                    )

        @self.on_edited_message()
        async def edit_message_event(client, event):
            if settings.database.edited_message:
                message = await self.database_message(event, delete=False)
                discuss_message = message.discuss_message

                if discuss_message:
                    pass
                    # if discuss_message.text:
                    #     try:
                    #         await self.edit_message_text(
                    #             discuss_message.chat.id,
                    #             message_id=discuss_message.id,
                    #             text=event.text,
                    #             entities=event.entities,
                    #         )
                    #     except:
                    #         log_stack.error(f't_text')
                    # elif discuss_message.caption:
                    #     try:
                    #         await self.edit_message_caption(
                    #             discuss_message.chat.id,
                    #             message_id=discuss_message.id,
                    #             caption=event.caption,
                    #             caption_entities=event.caption_entities,
                    #         )
                    #     except:
                    #         log_stack.error(f't_caption')

            if settings.discussion.forward.enable:
                if event.chat.id in self.discussion_fwd_data:
                    if self.discussion_fwd_data[event.chat.id].get('edit'):
                        await self.discuss_forward_edit(
                            events=[event, ],
                            data=self.discussion_fwd_data[event.chat.id]
                        )

        @self.on_deleted_messages()
        async def delete_message_event(client, events):
            if settings.database.deleted_message:
                await self.database_message(events, delete=True)

            if settings.discussion.forward.enable:
                # logger.info(f'{event=}')
                try:
                    chat_id = events[0].chat.id
                except:
                    log_stack.error(f'{events=}')
                    raise

                if chat_id in self.discussion_fwd_data:
                    if self.discussion_fwd_data[chat_id].get('delete'):
                        await self.discuss_forward_delete(
                            event=events,
                            data=self.discussion_fwd_data[chat_id]
                        )

                if chat_id == settings.discussion.chat_id:
                    await self.discuss_forward_delete(
                        event=events,
                        data=None,
                    )

                for message in events:

                    # if chat_id != settings.discussion.channel_id:
                    #     continue

                    # logger.info(f'try find discuss')
                    db_msg = self.db.select(
                        'message', message.chat.id,
                        id=message.id
                    )
                    # logger.info(f'{db_msg=}, {db_msg.discuss_message=}')
                    if not db_msg.discuss_message:
                        continue

                    await self.discuss_forward_delete(
                        event=[db_msg.discuss_message, ],
                        data=None,
                    )

        @self.on_poll()
        async def poll_update(client, raw_data):
            if settings.database.poll:
                logger.info(f'poll {raw_data=}')
                try:
                    await self.parse_poll(
                        message=None, raw_data=raw_data
                    )
                except:
                    pass

        @self.on_raw_update()
        async def raw_update(client, raw_data, raw_extra, raw_new):
            if settings.database.raw:
                # logger.info(f'{raw_data=}\n{raw_extra=}\n{raw_new=}')
                if isinstance(raw_data, pyrogram.raw.types.UpdateMessageReactions):
                    await self.parse_reactions(raw_data=raw_data)
