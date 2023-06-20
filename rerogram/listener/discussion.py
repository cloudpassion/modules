import asyncio
import re
import pyrogram

from collections import OrderedDict, namedtuple, deque

from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage
from pyrogram.errors.exceptions.flood_420 import FloodWait

from ..client import MyAbstractTelegramClient

from config import settings
from log import logger, log_stack


class MyTelethonChannelDiscussion(
    MyAbstractTelegramClient, PyrogramClient
):

    async def discuss_delete_message(
            self,
            message: PyrogramMessage,
            from_id: int,
    ):
        if settings.discussion.delete_info:
            if settings.discussion.delete_info_pm:
                await message.forward(
                    chat_id=from_id,
                )
                await self.send_message(
                    chat_id=from_id,
                    text='test deleteed pm text'
                )
            else:
                await message.reply(
                    text='test reply delete',
                )
        if settings.discussion.delete_noreply:
            await message.delete()

    async def discuss_new_message(
            self,
            message: PyrogramMessage
    ):

        chat_id = message.chat.id
        if chat_id != settings.discussion.chat_id:
            return

        from_user = message.from_user
        if from_user:
            from_id = from_user.id

        from_chat = message.sender_chat
        if from_chat:
            from_id = message.sender_chat.id

        if from_id == settings.discussion.channel_id:
            return

        if from_id == settings.discussion.chat_id:
            return

        _service = message.service

        if _service == pyrogram.enums.MessageServiceType.NEW_CHAT_MEMBERS:
            logger.info(f'new member join')
            return await self.discuss_delete_message(
                message, from_id
            )

        _top_id = message.reply_to_top_message_id
        _reply_id = message.reply_to_message_id

        reply_id = _top_id if _top_id else _reply_id if _reply_id else None

        logger.info(f'check reply: {reply_id=}, {chat_id=}')

        if not reply_id:
            return await self.discuss_delete_message(
                message, from_id
            )

        # db_reply_id = await self.db.select(
        #     'post',
        #     {
        #         'chat_id': chat_id,
        #         'chat_message_id': reply_id
        #     }
        # )
        #
        # logger.info(f'{_reply_id=}, {db_reply_id=}')
        #
        # if not db_reply_id:
        #     return await self.discuss_delete_message(
        #         client, message, from_id
        #     )

    async def delete_in_chat(self, _id, _start, _end):
        msg = await self.get_chat_messages(_id)
        await self.delete_messages(
            _id, message_ids=[x.id for x in msg[_start:_end]]
        )

    async def get_chat_messages(self, _id, count=None):
        msg = {}

        async for message in self.get_chat_history(_id):
            msg[message.id] = message

            if count:
                if len(msg) >= count:
                    break

        r_msg = []
        for k, v in OrderedDict(sorted(msg.items())).items():
            r_msg.append(v)

        return r_msg

    async def discuss_init(
            self, channel_id, chat_id, first=False
    ):

        # found first message
        msg = await self.get_chat_messages(channel_id)
        first_message = msg[0] if msg else None
        messages_count = len(msg)
        logger.info(f'{first_message=}\n{messages_count=}')

        async def refactor_post_text(
                num, text, _chat_id=None, _channel_id=None
        ):
            if text and f'reserve_{num}' not in text:
                for find in re.findall(
                        '(post_[\d+].*?)[\n| |)]',
                        text
                ):
                    logger.info(f'{find=}')
                    try:
                        db_data = await self.db.select(
                            'post',
                            {
                                'channel_id': _channel_id,
                                'chat_id': _chat_id,
                                'post_id': find.split('_')[1]
                            }
                        )
                        if not db_data:
                            continue

                        post_id = db_data.channel_message_id
                        text = text.replace(
                            find, f'{post_id}'
                        )
                    except:
                        log_stack.error(f'check')

            return text

        async def get_settings_post_data(
                num,
                _chat_id=None, _channel_id=None,
        ):
            _post_values = {
                k: {} for k in (
                    'text', 'photo', 'info', 'skip_edit'
                )
            }
            post_data = namedtuple(
                'post_data',
                (k for k in _post_values.keys())
            )
            try:
                post = getattr(settings.discussion.init, f'post_{num}')
            except:
                return post_data._make(
                    (None for x in _post_values.keys())
                )

            try:
                _post_values['text'] = getattr(post, f'text')
                if 'txt' in _post_values['text']:
                    try:
                        with open(_post_values['text'], 'r') as tr:
                            _post_values['text'] = tr.read()
                    except:
                        pass
            except:
                _post_values['text'] = f'reserve_{num}'

            for key in _post_values:
                if key in 'text':
                    continue
                try:
                    _post_values[key] = getattr(post, f'{key}')
                except Exception:
                    if key == 'photo':
                        _post_values[key] = getattr(settings.discussion.init, f'{key}')
                    else:
                        _post_values[key] = None

            return post_data._make((
                *(v for v in _post_values.values()),
            ))

        async def init_messages(init_message, count):
            num = len(init_message)-1
            while num != count:

                num += 1
                try:
                    message = init_message[num]
                    if message and message.service:
                        continue
                except:
                    pass

                logger.info(f'{num=}')

                post_data = await get_settings_post_data(num)
                text = post_data.text
                photo = post_data.photo
                while True:
                    try:
                        if photo:
                            await self.send_photo(
                                chat_id=channel_id, caption=text, photo=photo,
                            )
                        elif text:
                            await self.send_message(
                                chat_id=channel_id, text=text
                            )
                        else:
                            await self.send_photo(
                                chat_id=channel_id, caption=f'reserve_{num}',
                                photo='init.png',
                            )
                        break
                    except FloodWait as exc:
                        logger.info(f'flood: {exc}')
                        await asyncio.sleep(30)

        async def unpin_in_chat(_id, unpin_messages):
            for pinned in unpin_messages[1:]:
                logger.info(f'{pinned=}')

                if pinned.id != unpin_messages[0].id:
                    await self.unpin_chat_message(_id, message_id=pinned.id)

        if first:
            pass
        else:
            if settings.discussion.posts_delete:
                _start = settings.discussion.posts_delete[0]
                _end = settings.discussion.posts_delete[1]
                await self.delete_in_chat(channel_id, _start, _end)

            if messages_count < settings.discussion.posts_count:
                await init_messages(
                    await self.get_chat_messages(
                        channel_id,
                    ),
                    settings.discussion.posts_count,
                )
            # await unpin_in_chat(
            #     chat_id,
            #     await self.get_chat_messages(chat_id, 2, 1024),
            # )

        after_init_channel_msg = await self.get_chat_messages(
            channel_id,
        )

        async def check_post_text(
                _channel_id,
                _chat_id,
                channel_messages,
        ):
            num = 0
            channel_messages = deque(channel_messages)
            while num != len(channel_messages)+1:

                try:
                    message = channel_messages.popleft()
                except IndexError:
                    break

                message: PyrogramMessage
                if message.service:
                    continue

                num += 1
                # logger.info(f'{num=}, {message=}')

                post_data = await get_settings_post_data(
                    num, _chat_id=_chat_id, _channel_id=_channel_id,
                )
                text = message.text if message.text else message.caption if message.caption else ''
                refactor_text = await refactor_post_text(
                    num, text=text, _chat_id=_chat_id, _channel_id=_channel_id,
                )
                if post_data.skip_edit:
                    if text == refactor_text:
                        continue

                    send_text = refactor_text
                else:
                    send_text = await refactor_post_text(
                        num, text=post_data.text, _chat_id=_chat_id,
                        _channel_id=_channel_id
                    )

                if send_text and text != send_text:
                    if message.caption:
                        await message.edit_caption(
                            caption=send_text
                        )
                    else:
                        await message.edit_text(
                            text=send_text
                        )

        async def check_post_comment(
                channel_id,
                chat_id,
                channel_messages,
                limit=settings.discussion.posts_count,
        ):
            if limit > 30:
                sleep_time = 0.5
            else:
                sleep_time = 0

            if settings.discussion.comments_delete:
                _comments_delete = [
                    channel_messages[x] for x in range(
                        *settings.discussion.comments_delete
                    )
                ]
            else:
                _comments_delete = False

            if _comments_delete:
                comments_delete = []
                for msg in _comments_delete:
                    msg_id = msg.id
                    while True:
                        try:
                            async for reply in self.get_discussion_replies(
                                    channel_id,
                                    message_id=msg_id,
                                    limit=1,
                            ):
                                logger.info(f'{reply=}')
                                comments_delete.append(reply.id)
                                await asyncio.sleep(0.5)
                            break
                        except FloodWait as exc:
                            logger.info(f'flood: {exc=}')
                            await asyncio.sleep(30)

                await self.delete_messages(
                    chat_id=chat_id, message_ids=comments_delete,
                )

            num = 0
            channel_messages = deque(channel_messages[:limit+1])
            while num != len(channel_messages)+1:

                try:
                    channel_message = channel_messages.popleft()
                except IndexError:
                    break

                channel_message: PyrogramMessage
                if channel_message.service:
                    continue

                num += 1

                db_data = await self.db.select(
                    'post',
                    {
                        'channel_id': channel_id,
                        'channel_message_id': channel_message.id
                    },
                )
                reply = None
                if not db_data:
                    async for reply in self.get_discussion_replies(
                        channel_id,
                        message_id=channel_message.id,
                        limit=1,
                    ):
                        pass
                    await asyncio.sleep(sleep_time)
                else:
                    exists = await self.get_messages(
                        chat_id, [db_data.chat_comment_id, ]
                    )
                    if exists:
                        reply = db_data
                        reply.outgoing = True

                post_data = await get_settings_post_data(num)
                if reply:
                    if not reply.outgoing:
                        continue
                else:
                    if post_data.info:
                        info = post_data.info
                    else:
                        info = 'reserve'

                    chat_msg = await self.get_discussion_message(
                        channel_id,
                        message_id=channel_message.id,
                    )
                    new_reply = await chat_msg.reply(
                        text=info,
                    )
                    self.db.add_data(
                        'post',
                        {
                            'channel_id': channel_id,
                            'channel_message_id': channel_message.id
                        },
                        chat_id=chat_msg.chat.id,
                        chat_message_id=chat_msg.id,
                        chat_comment_id=new_reply.id,
                        text=info,
                        caption=None,
                        post_id=num,
                        force_update=True,
                    )
                    continue

                text = reply.text if reply.text else reply.caption if reply.caption else ''
                if not db_data:
                    chat_msg = await self.get_discussion_message(
                        channel_id,
                        message_id=channel_message.id,
                    )
                    self.db.add_data(
                        'post',
                        {
                            'channel_id': channel_id,
                            'channel_message_id': channel_message.id
                        },
                        chat_id=reply.chat.id,
                        chat_message_id=chat_msg.id,
                        chat_comment_id=reply.id,
                        text=reply.text,
                        caption=reply.caption,
                        post_id=num,
                        force_update=True,
                    )

                if not post_data.info:
                    continue

                if text == post_data.info:
                    continue

                if reply.caption:
                    caption = reply.caption
                    text = None
                else:
                    caption = None
                    text = post_data.info

                if isinstance(reply, PyrogramMessage):
                    chat_msg = await self.get_discussion_message(
                        channel_id,
                        message_id=channel_message.id,
                    )
                    _message_id = chat_msg.id
                    _chat_id = reply.chat.id
                else:
                    _message_id = reply.chat_message_id
                    _chat_id = reply.chat_id

                if caption:
                    new_reply = await self.edit_message_caption(
                        chat_id=_chat_id,
                        message_id=_message_id,
                        caption=caption,
                    )
                else:
                    new_reply = await self.edit_message_text(
                        chat_id=_chat_id,
                        message_id=_message_id,
                        text=text,
                    )

                self.db.add_data(
                    'post',
                    {
                        'channel_id': channel_id,
                        'channel_message_id': channel_message.id
                    },
                    chat_id=_chat_id,
                    chat_message_id=_message_id,
                    chat_comment_id=new_reply.id,
                    text=text,
                    caption=caption,
                    post_id=num,
                    force_update=True,
                )

        await check_post_text(
            channel_id,
            chat_id,
            after_init_channel_msg,
        )
        if settings.discussion.check_post_comments:
            await check_post_comment(
                channel_id,
                chat_id,
                after_init_channel_msg,
            )



