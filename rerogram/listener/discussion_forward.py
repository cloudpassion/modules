import asyncio
import re
import pyrogram
import ujson as json

from datetime import datetime
from typing import Union
from collections import OrderedDict, namedtuple, deque

from asgiref.sync import sync_to_async, async_to_sync
from pyrogram.raw.types.channel import Channel
from pyrogram.raw.types.chat import Chat
from pyrogram.raw.types.user import User

from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage, InputMediaPhoto
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import FileReferenceExpired
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

from ..client import MyAbstractTelegramClient

from ..functions.stuff import progress


from ..django_telegram.django_telegram.datamanager.models import (
    ForwardedToDiscuss, Message
)

from atiny.data import chunks
from config import settings
from log import logger, log_stack


class MyTelethonChannelDiscussionForward(
    MyAbstractTelegramClient, PyrogramClient
):

    async def get_media_kwargs(
            self,
            event: PyrogramMessage,
            skip_keys=[],
    ):

        kwargs = {}
        if not hasattr(event, 'media') or not event.media:
            return kwargs

        for k in self.media_kwargs.get(event.media):
            if k in skip_keys:
                continue

            if hasattr(event, k):
                value = getattr(event, k)
                kwargs.update(
                    {
                        k: value
                    }
                )

        return kwargs

    async def reupload_file(
            self, message_kwargs, media_type,
    ):

        # kwargs = {
        #     'photo': pyrogram.types.Photo(
        #         file_id='',
        #         file_unique_id='AgADhMExGyJWiEo',
        #         width=720, height=1280, file_size=102286,
        #         date=datetime.datetime(2022, 10, 20, 10, 31, 17),
        #         thumbs=[
        #             pyrogram.types.Thumbnail(
        #                 file_id='',
        #                 file_unique_id='AgADhMExGyJWiEo',
        #                 width=180, height=320, file_size=12679)
        #         ])
        # }

        logger.info(f'1{message_kwargs=}')
        file_id = await self.get_file_id(message_kwargs)
        media_class = type(message_kwargs.get(media_type))

        logger.info(f'{media_type=}')
        logger.info(f'{media_class=}')

        file_name = f'{settings.download.tmp_dir}/{file_id[12:25]}'\
                    f'.{self.media_ext.get(media_class)}'
        file_data = await self.download_media(
            await self.get_file_id(message_kwargs),
            # in_memory=True,
            in_memory=False,
            progress=progress,
            file_name=file_name,
        )
        logger.info(f'{file_data=}')

        # media_class = self.self.media_fwd_class()
        # reupload = await self.save_file(
        #     # file_data,
        #     f'{settings.download.tmp_dir}/{file_id}',
        #     progress=progress
        # )
        # logger.info(f'{reupload=}')

        # setattr(reupload, 'file_id', reupload.name)
        # reupload.file_id = reupload.name

        # setattr(message_kwargs[media_type], 'file_id', reupload.name)
        message_kwargs[media_type] = file_name
        #     .update(
        #     {
        #         media_type: reupload,
        #     }
        # )
        logger.info(f'2{message_kwargs=}')

        return message_kwargs

    async def get_file_id(self, kwargs):
        for k, v in kwargs.items():
            if hasattr(v, 'file_id'):
                return v.file_id

    async def replace_if_file_id(
            self, kwargs,
    ):
        return {
            **{k: v.file_id for k, v in kwargs.items() if hasattr(v, 'file_id')},
        }

    async def discuss_forward_delete(
            self,
            event: Union[PyrogramMessage, list], data, destroy=False,
    ):

        delete_ids = []
        delete_chat_id = None
        for message in event:

            _db_message = self.db.select(
                'message', message.chat.id,
                id=message.id,
            )
            if not _db_message:
                continue

            if _db_message.media_group_id:
                db_group = await self.get_media_group_db(
                    _db_message.chat.id,
                    _db_message.id,
                )
            else:
                db_group = [_db_message, ]

            for db_message in db_group:
                # search = {
                #     'from_event': db_message,
                # }
                # db_msg: ForwardedToDiscuss = self.db.select(
                #     'ForwardedToDiscuss',
                #     search,
                # )
                #
                # # logger.info(f'11{db_msg=}, {message.chat.id=}, {message.id=}')
                # if not db_msg:
                search = {
                    'from_message': db_message,
                }
                db_msg: ForwardedToDiscuss = self.db.select(
                    'ForwardedToDiscuss',
                    search,
                )
                # logger.info(f'22{db_msg=}, {message.chat.id=}, {message.id=}')

                if not db_msg:
                    search = {
                        'message': db_message,
                    }
                    db_msg: ForwardedToDiscuss = self.db.select(
                        'ForwardedToDiscuss',
                        search,
                    )
                    # logger.info(f'33{db_msg=}, {message.chat.id=}, {message.id=}')

                if not db_msg:
                    continue

                delete_ids.append(
                    db_msg.message.id,
                )
                if db_msg.group_ids:
                    delete_ids.extend(json.loads(db_msg.group_ids))

                delete_chat_id = db_msg.chat.id
                if destroy:
                    db_msg.delete()
                else:
                    db_msg.deleted = True
                    db_msg.save(force_update=True)

        # logger.info(f'{delete_chat_id=}, {delete_ids=}')
        if delete_ids and delete_chat_id:
            await self.delete_messages(
                delete_chat_id, message_ids=set(delete_ids)
            )

    async def discuss_forward_edit(
            self,
            events: Union[PyrogramMessage, list], data
    ):

        new_events = list(chunks(events, 200))
        logger.info(f'fwd_edit: {len(events)=}')
        # if len(events) > 200:
        #     events = events[-200:]

        db_return = []
        for events in new_events:

            db_data = []
            for event in events:

                tr = 0
                sl_t = 0.1
                while True:
                    db_message = self.db.select(
                        'message', event.chat.id,
                        id=event.id,
                    )
                    if db_message:
                        break

                    logger.info(f'wait db')
                    await asyncio.sleep(sl_t)
                    tr += 1
                    if tr % 1000 == 0:
                        sl_t += 1

                # if not db_msg:
                search = {
                    'from_message': db_message,
                }
                db_msg: ForwardedToDiscuss = self.db.select(
                    'ForwardedToDiscuss',
                    search,
                )
                logger.info(f'1{db_message=}, {db_msg=}, {event.chat.id=}, {event.id=}')

                # if not db_msg:
                #     search = {
                #         'from_event': db_message,
                #     }
                #     db_msg: ForwardedToDiscuss = self.db.select(
                #         'ForwardedToDiscuss',
                #         search,
                #     )
                # logger.info(f'2{db_msg=}, {event.chat.id=}, {event.id=}')

                db_data.append(
                    (db_msg, event, search)
                )

            message_ids = [x[0].message.id for x in db_data if x[0]]
            if message_ids:
                while True:
                    try:
                        check_msg = {
                            x.id: x for x in (
                                await self.get_messages(
                                    settings.discussion.chat_id,
                                    message_ids=message_ids,
                                )
                            )
                        }
                        break
                    except FloodWait as exc:
                        await self.parse_flood('fwd_get_msg', exc)
                    except Exception as exc:
                        log_stack.error(f'gmsg')
                        await asyncio.sleep(30)

            else:
                check_msg = {}

            for _data in db_data:
                new_db_msg = _data[0]
                event = _data[1]
                search = _data[2]

                if not new_db_msg:
                    db_return.append(
                        (None, event)
                    )
                    continue

                # logger.info(f'{event.id=}, {db_msg.chat.id=}, {db_msg.message.id=}\n')

                if new_db_msg.deleted:
                    logger.info(f'not_edit deleted {new_db_msg=}')
                    db_return.append(
                        (True, event)
                    )
                    continue

                if not check_msg.get(new_db_msg.message.id):
                    await self.discuss_forward_delete(
                        [event, ], data,
                    )
                    db_return.append(
                        (True, event),
                    )
                    continue

                # if not check_msg or (len(check_msg) == 1 and check_msg[0].empty):
                if check_msg[new_db_msg.message.id].empty:
                    await self.discuss_forward_delete(
                        [event, ], data,
                    )
                    db_return.append(
                        (True, event),
                    )
                    continue

                to_who = None
                from_reply_id = None
                reply_to = data.reply_to

                if 'reply' in reply_to:

                    if reply_to == 'reply_id':
                        from_reply_id = event.reply_to_message_id
                    elif reply_to == 'reply_top_id':
                        from_reply_id = event.reply_to_top_message_id
                        if not from_reply_id:
                            from_reply_id = event.reply_to_message_id
                    else:
                        from_reply_id = None

                if from_reply_id:
                    to_reply_id, to_who = await self.get_to_reply(
                        'to_who', event, from_reply_id, to_who,
                    )

                try:
                    reply_mention = data.reply_mention
                except:
                    reply_mention = False

                from_who = getattr(
                    event, 'sender_chat'
                ) if event.sender_chat else getattr(
                    event, 'from_user'
                ) if event.from_user else None

                post_text = new_db_msg.post_text
                _post_text, from_name, to_name = await self.get_post_comment(
                    event, data, from_who=from_who,
                    to_who=to_who if reply_mention else None,
                )
                if _post_text != post_text:
                    post_text = _post_text

                if reply_mention and to_name:
                    user_mentions = [
                        ('TEXT_MENTION', to_name, to_who, -1),
                    ]
                elif from_who:
                    user_mentions = [
                        ('TEXT_MENTION', from_name, from_who, -1),
                    ]
                else:
                    user_mentions = []

                edited = False
                new_text = {}
                if event.text:
                    _clear_text = event.text.replace(
                        new_db_msg.post_text, '').replace(post_text, '')
                    text = f'{_clear_text}'
                    temp = f'\n\n{post_text}'

                    if len(text) + len(temp) < 4096:
                        text += temp

                    else:
                        text = "".join(
                            text[0:(4096-len(temp)-1)]
                        ) + temp

                    new_entities, _t, entities_edited = await self.add_entites(
                        text=text,
                        text_mentions=user_mentions,
                        old_entities=event.entities,
                    )

                    if (
                            (
                                    event.text != check_msg[
                                        new_db_msg.message.id
                                    ].text
                            ) or (
                            post_text != new_db_msg.post_text
                            ) or entities_edited
                    ):
                        new_text.update({
                            'post_text': post_text,
                        })

                        wait = True
                        while True:
                            try:
                                if check_msg[
                                    new_db_msg.message.id
                                ].text and text != check_msg[
                                        new_db_msg.message.id].text:
                                    try:
                                        edit_fwd = await self.edit_message_text(
                                            new_db_msg.chat.id,
                                            message_id=new_db_msg.message.id,
                                            text=text,
                                            entities=new_entities,
                                            disable_web_page_preview=True,
                                        )
                                        edited = True
                                        break
                                    except FloodWait as exc:
                                        await self.parse_flood('fwd_edit_msg', exc, wait=wait)
                                        if not wait:
                                            break
                                    except MessageNotModified:
                                        edited = True
                                        break
                                    except pyrogram.errors.exceptions.forbidden_403.MessageAuthorRequired:
                                        logger.info(f'not author of {new_db_msg.message.id}')
                                        await asyncio.sleep(60)
                                        break
                                else:
                                    break
                            except:
                                log_stack.error(f'see')
                                pass

                if event.caption:

                    _clear_text = event.caption.replace(
                        new_db_msg.post_text, '').replace(post_text, '')
                    caption = f'{_clear_text}'
                    temp = f'\n\n{post_text}'

                    if len(caption) + len(temp) < 1024:
                        caption += temp

                    else:
                        caption = "".join(
                            caption[0:(1024-len(temp)-1)]
                        ) + temp

                    new_entities, _t, entities_edited = await self.add_entites(
                        text=caption,
                        text_mentions=user_mentions,
                        old_entities=event.entities,
                    )
                    if (
                        (
                                event.caption != check_msg[
                                    new_db_msg.message.id
                                ].caption
                        ) or (
                            post_text != new_db_msg.post_text
                        ) or entities_edited
                    ):

                        new_text.update({
                            'post_text': post_text,
                        })
                        wait = True
                        while True:
                            try:
                                if check_msg[
                                    new_db_msg.message.id
                                ].caption and caption != check_msg[
                                        new_db_msg.message.id
                                ].caption:
                                    try:
                                        edit_fwd = await self.edit_message_caption(
                                            new_db_msg.chat.id,
                                            message_id=new_db_msg.message.id,
                                            caption=caption,
                                            caption_entities=new_entities,
                                        )
                                        edited = True
                                        break
                                    except FloodWait as exc:
                                        await self.parse_flood('fwd_edit_msg', exc, wait=wait)
                                        if not wait:
                                            break
                                    except MessageNotModified:
                                        edited = True
                                        break
                                    except pyrogram.errors.exceptions.forbidden_403.MessageAuthorRequired:
                                        logger.info(f'not author of {new_db_msg.message.id}')
                                        await asyncio.sleep(60)
                                        break
                                else:
                                    break
                            except:
                                log_stack.error(f'see')
                                pass

                if edited:
                    self.db.add_data(
                        'ForwardedToDiscuss',
                        search,
                        **{
                            **new_text,
                            'edit_date': datetime.now(),
                        }, force_update=True
                    )

                db_return.append(
                    (True, event)
                )

        return db_return

    async def discuss_forward_new(
            self,
            event: PyrogramMessage, data,
    ):
        logger.info(f'ENTER FORWARD, {event.id=}, {event.media_group_id=}, '
                    f'{event.media=}')

        _media_messages = []
        if event.media_group_id:
            if not self.fwd_skip_group.get(
                    event.media_group_id
            ):
                self.fwd_skip_group[event.media_group_id] = True
            else:
                logger.info(f'fwd RETURN')
                return

            _media_messages = await self.get_media_group_db(
                chat_id=event.chat.id,
                media_group_id=event.media_group_id,
                net=True, cache=False,
            )

            logger.info(f'{[x.id for x in _media_messages]=}')
            logger.info(f'{[x.caption for x in _media_messages]=}')
            _event_to_post = [x for x in _media_messages if x.caption]
            if _event_to_post:
                event_to_post = _event_to_post[0]
            else:
                event_to_post = event

            event_comment = _media_messages[0]
        else:
            _media_messages = []
            event_to_post = event
            event_comment = event

        try:
            skip_no_reply = data.skip_no_reply
        except:
            skip_no_reply = []

        try:
            skip_from_users = data.skip_from_users
        except:
            skip_from_users = []

        from_who: Union[User, Channel, Chat] = getattr(
            event, 'sender_chat'
        ) if event.sender_chat else getattr(
            event, 'from_user'
        ) if event.from_user else None

        to_who = None

        if hasattr(event, 'from_user') and event.from_user:
            if skip_from_users or event.from_user in skip_from_users:
                if not event.reply_to_message_id and not event.reply_to_top_message_id:
                    logger.info(f'skip no reply from_user: {event.from_user=}, {event.id=}')
                    return

        if from_who and from_who.id in skip_no_reply:
            if not event.reply_to_message_id and not event.reply_to_top_message_id:
                logger.info(f'skip no reply from_who: {from_who=}, {event.id=}')
                return

        to_chat_id = settings.discussion.chat_id

        forwarded = []
        to_reply_id = None

        messages = []
        reply_to = data.reply_to
        if reply_to == 'top_id':
            to_reply_id = data.top_id

        elif 'reply' in reply_to:

            if reply_to == 'reply_id':
                from_reply_id = event.reply_to_message_id
            elif reply_to == 'reply_top_id':
                from_reply_id = event.reply_to_top_message_id
                if not from_reply_id:
                    from_reply_id = event.reply_to_message_id
            else:
                from_reply_id = None

            if from_reply_id:
                to_reply_id, to_who = await self.get_to_reply(
                    None, event, from_reply_id, to_who,
                )

            if not to_reply_id and hasattr(data, 'no_reply'):
                to_reply_id = getattr(data, data.no_reply)

            if not to_reply_id:
                to_reply_id = data.fail_id

        if not to_reply_id:
            logger.info(f'cant find reply')
            return

        try:
            reply_mention = data.reply_mention
        except:
            reply_mention = False

        post_text, from_name, to_name = await self.get_post_comment(
            event_comment, data, from_who=from_who,
            to_who=to_who if reply_mention else None,
        )

        if reply_mention and to_name:
            user_mentions = [
                ('TEXT_MENTION', to_name, to_who, -1),
            ]
        elif from_who:
            user_mentions = [
                ('TEXT_MENTION', from_name, from_who, -1),
            ]
        else:
            user_mentions = []

        if event.text:
            send_text = f'{event.text if event.text else ""}'
            temp = f'\n\n{post_text}'
            if len(send_text) + len(temp) < 4096:
                send_text += temp

            else:
                send_text = "".join(
                    send_text[0:(4096-len(temp)-1)]
                ) + temp

            new_entities, _t, _tt = await self.add_entites(
                    text=f'{send_text}',
                    text_mentions=user_mentions,
                    old_entities=event.entities,
            )
            while True:
                try:

                    fwd_msg = await self.send_message(
                        chat_id=to_chat_id,
                        text=f'{send_text}',
                        reply_to_message_id=to_reply_id,
                        entities=new_entities,
                        disable_web_page_preview=True,
                    )
                    await self.database_message(
                        message=fwd_msg,
                    )
                    break
                except FloodWait as exc:
                    await self.parse_flood('fwd_send_msg', exc)
                except pyrogram.errors.exceptions.bad_request_400.PeerIdInvalid:
                    logger.info(f'unknow peer_id: {new_entities}')
                    new_entities, _t, _tt = await self.add_entites(
                        text=f'{send_text}',
                        old_entities=event.entities,
                    )
                except KeyError as exc:
                    if 'ID not found' in f'{exc}':
                        logger.info(f'unknow peer_id: {new_entities}')
                        new_entities, _t, _tt = await self.add_entites(
                            text=f'{send_text}',
                            old_entities=event.entities,
                        )
                    else:
                        log_stack.error(f'ch1.1')
                        await asyncio.sleep(120)
                except Exception as exc:
                    log_stack.error(f'ch1')
                    await asyncio.sleep(120)

            forwarded.append(fwd_msg)
            messages.append(event)

        elif event.poll:
            poll_text = f'Голосование (Ссылка в конце сообщения).\n\n'\
                        f'{event.poll.question}\n\n'\
                        f'{post_text}'
            new_entities, _t, _tt = await self.add_entites(
                text=poll_text,
                text_mentions=user_mentions,
            )
            while True:
                try:
                    fwd_msg = await self.send_message(
                        chat_id=to_chat_id,
                        text=poll_text,
                        entities=new_entities,
                        reply_to_message_id=to_reply_id,
                        disable_web_page_preview=True,
                    )
                    await self.database_message(
                        message=fwd_msg,
                    )
                    break
                except FloodWait as exc:
                    await self.parse_flood('fwd_send_msg', exc)
                except pyrogram.errors.exceptions.bad_request_400.PeerIdInvalid:
                    logger.info(f'unknow peer_id: {new_entities}')
                    new_entities, _t, _tt = await self.add_entites(
                        text=poll_text,
                    )
                except KeyError as exc:
                    if 'ID not found' in f'{exc}':
                        logger.info(f'unknow peer_id: {new_entities}')
                        new_entities, _t, _tt = await self.add_entites(
                            text=poll_text,
                        )
                    else:
                        log_stack.error(f'ch1.1')
                        await asyncio.sleep(120)
                except Exception as exc:
                    log_stack.error(f'ch2')
                    await asyncio.sleep(120)

            forwarded.append(fwd_msg)
            messages.append(event)

        elif (
                (
                    event.sticker
                ) or (
                    event.animation
                ) or (
                    event.contact
                ) or (
                    event.video_note
                ) or (
                    event.location
                )
        ):
            logger.info(f'md: {event.media=}')
            kwargs = await self.get_media_kwargs(
                event, [
                    'caption', 'caption_entities',
                    'disable_web_page_preview',
                ]
            )

            func = self.media_functions.get(event.media)
            while True:
                try:
                    fwd_msg = await func(
                        chat_id=to_chat_id,
                        reply_to_message_id=to_reply_id,
                        **await self.replace_if_file_id(
                            kwargs,
                        ),
                        **{
                            k: getattr(
                                getattr(event, self.media_type_kw.get(event.media)), k) for k in self.media_kwargs.get(
                                event.media
                            ) if k != self.media_type_kw.get(event.media)
                        },
                    )
                    await self.database_message(
                        message=fwd_msg,
                    )
                    break
                except FloodWait as exc:
                    await self.parse_flood('st_send_msg', exc)
                except pyrogram.errors.exceptions.bad_request_400.ChatForwardsRestricted:
                    logger.info(f'forward_restrict: {to_chat_id}')
                    break
                except FileReferenceExpired:
                    raise FileReferenceExpired
                except Exception as exc:
                    log_stack.error(f'chst3')
                    await asyncio.sleep(120)

            forwarded.append(fwd_msg)
            messages.append(event)

        elif event.media:

            if _media_messages:
                media_messages = _media_messages
            else:
                media_messages = [event, ]

            for n, message in enumerate(media_messages):

                if n == 0:
                    if event_to_post.caption:
                        caption = f'{event_to_post.caption if event_to_post.caption else ""}'
                        temp = f'\n\n{post_text}'

                        if len(caption) + len(temp) < 1024:
                            caption += temp

                        else:
                            caption = "".join(
                                caption[0:(1024-len(temp)-1)]
                            ) + temp

                        caption_entities, _t, _tt = await self.add_entites(
                            text=caption,
                            text_mentions=user_mentions,
                            old_entities=event.caption_entities,
                        )
                    else:
                        caption = f'{post_text}'
                        caption_entities, _t, _tt = await self.add_entites(
                            text=caption,
                            text_mentions=user_mentions,
                        )
                else:
                    caption = f'{post_text}'
                    caption_entities, _t, _tt = await self.add_entites(
                        text=caption,
                        text_mentions=user_mentions,
                    )

                kwargs = await self.get_media_kwargs(
                    message, [
                        'caption', 'caption_entities',
                        'disable_web_page_preview',
                    ]
                )

                media_kwargs = await self.replace_if_file_id(
                    kwargs,
                )

                while True:
                    try:
                        func = self.media_functions.get(message.media)

                        fwd_msg = await func(
                            chat_id=to_chat_id,
                            reply_to_message_id=to_reply_id,
                            caption=caption,
                            caption_entities=caption_entities,
                            **media_kwargs,
                            **{
                                  k: getattr(
                                      getattr(
                                          message, self.media_type_kw.get(
                                              message.media
                                          )), k
                                  ) for k in self.media_kwargs.get(
                                      message.media
                                  ) if k != self.media_type_kw.get(message.media)
                              },
                        )
                        await self.database_message(
                            message=fwd_msg,
                        )
                        break
                    except FloodWait as exc:
                        await self.parse_flood('fwd_send_msg', exc)
                    except FileReferenceExpired:
                        raise FileReferenceExpired
                    except pyrogram.errors.exceptions.bad_request_400.ChatForwardsRestricted:
                        logger.info(f'forward_restrict: {to_chat_id}')
                        media_kwargs = await self.reupload_file(
                            kwargs, self.media_type_kw.get(message.media)
                        )
                        await asyncio.sleep(5)
                    except Exception as exc:
                        log_stack.error(f'ch3: {to_chat_id}, {kwargs=}')
                        await asyncio.sleep(120)

                forwarded.append(fwd_msg)
                messages.append(message)

        for msg, forward in zip(messages, forwarded):

            while True:
                db_msg = self.db.select(
                    'message', msg.chat.id,
                    id=msg.id,
                )
                if db_msg:
                    break
                logger.info(f'sl1')
                await asyncio.sleep(0.1)

            while True:
                db_forward = self.db.select(
                    'message', forward.chat.id,
                    id=forward.id,
                )
                if db_forward:
                    break
                logger.info(f'sl2')
                await asyncio.sleep(0.1)

            while True:
                db_event = self.db.select(
                        'message', event.chat.id,
                        id=event.id,
                    )

                if db_event:
                    break
                logger.info(f'sl3')
                await asyncio.sleep(0.1)

            self.db.add_data(
                'ForwardedToDiscuss',
                {
                    'message': db_forward,
                },
                **{
                    'hint': data.hint,

                    'from_message': db_msg,
                    'event_message': db_event,

                    'from_chat': db_msg.chat,
                    'chat': db_forward.chat,
                    'post_text': post_text,

                    'group_ids': [x.id for x in forwarded],

                    'date': datetime.now(),

                }
            )
