import pyrogram
import asyncio
import os.path

from collections import defaultdict, namedtuple, deque
from typing import Union
from asgiref.sync import sync_to_async, async_to_sync

from ..django_telegram.django_telegram.datamanager.models import (
    TgFile, TgPhoto, TgVideo, TgVoice, TgAudio, TgSticker,
    TgThumb,
)
from ..db.schemas.django import MyDjangoORM
from pyrogram.types import Message
from pyrogram.client import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage


from atiny.file import FileUtils, create_dirname
from config import settings
from log import logger, log_stack

from ..client.entities import MyPyrogramEntities
from ..client.logging import MyPyrogramLogging


FL_CLASSES = {
    'photo': TgPhoto,
    'document': TgFile,
    'video': TgVideo,
    'voice': TgVoice,
    'audio': TgAudio,
    'chat_photo': TgPhoto,
    'user_photo': TgPhoto,
    'sticker': TgSticker,
    'thumb': TgThumb,

}

FL_EFIELDS = {
    'chat_photo': {
        'main_id': 'big_file_id',
        'unique_id': 'big_photo_unique_id',
        'db_keys': (
            'small_file_id', 'small_photo_unique_id',
            'big_file_id', 'big_photo_unique_id'
        ),
    },
    'user_photo': {
        'main_id': 'big_file_id',
        'unique_id': 'big_photo_unique_id',
        'db_keys': (
            'small_file_id', 'small_photo_unique_id',
            'big_file_id', 'big_photo_unique_id'
        ),
    },
    'photo': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'date',
        )
    },
    'document': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
           'file_id', 'file_unique_id', 'file_name', 'mime_type',
        )
    },
    'video': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'file_name', 'mime_type',
        )
    },
    'voice': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'duration', 'waveform', 'mime_type',
        )
    },
    'audio': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'duration', 'file_name', 'mime_type',
        )
    },
    'sticker': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'file_name', 'mime_type', 'emoji',
            'set_name', 'is_animated',
        )
    },
    'thumb': {
        'main_id': 'file_id',
        'unique_id': 'file_unique_id',
        'db_keys': (
            'file_id', 'file_unique_id', 'width', 'height',
        )
    },
}


class MyAbstractTelegramClient(
    MyPyrogramEntities,
    MyPyrogramLogging,
):
    forward_from_to: defaultdict
    log_session_file: str
    chats_db: dict
    db: Union[MyDjangoORM, ]
    chat_data: defaultdict = defaultdict(lambda: {}, {})
    discussion_fwd_data: dict

    async def download_file(
            self, fl_data=None, client: PyrogramClient = None,
            message: Message = None, files=None,
            _att=[], add_id='/', info_name=None, log=True,
    ):

        async def progress(current, total):
            try:
                logger.info(f"{current * 100 / total:.1f}%")
            except:
                pass

        if not fl_data and not message and not client:
            return files

        file_type = fl_data.tp
        fl_class = FL_CLASSES[file_type]

        files = [] if not files else files

        try:
            file_db: Union[
                TgFile, TgPhoto,
            ] = fl_class.objects.filter(
                file_unique_id=getattr(fl_data, FL_EFIELDS[file_type]['unique_id'])
            ).first()
            # if log:
            #     logger.info(f'file_dd_exists:{file_db=}')

            force_update = False
            if file_db:
                new_fl = namedtuple(
                    'new_fl', (
                        'file_data', 'file_path', 'file_dir', 'saved', 'main_id',
                        'unique_id',
                        'fl_class', 'md5', 'file_size', 'tg_size', 'force_update',
                        'db_keys',
                        *FL_EFIELDS[file_type]['db_keys'],
                        *(x for x in _att if x != 'tp'),
                    )
                )
                try:
                    saved = os.stat(
                        file_db.path, follow_symlinks=True
                    ).st_size != 0
                except:
                    saved = False

                if saved and file_db.md5 in file_db.path:
                    files.append(
                        new_fl._make((
                            None, file_db.path,
                            f'{settings.download.download_dir}{add_id}',
                            saved,
                            FL_EFIELDS[file_type]['main_id'],
                            FL_EFIELDS[file_type]['unique_id'],
                            fl_class, file_db.md5, file_db.size,
                            fl_data.tg_size,
                            force_update,
                            (
                                *FL_EFIELDS[file_type]['db_keys'],
                                *(x for x in _att if x != 'tp'),
                            ),
                            *(getattr(fl_data, x) for x in FL_EFIELDS[file_type]['db_keys']),
                            *(getattr(fl_data, x) for x in _att if x != 'tp'),
                        ))
                    )
                    return files
                else:
                    force_update = True
            else:
                force_update = True
        except:
            force_update = True
            log_stack.error(f'chk')

        if client and fl_data.file_id:
            file_data = await client.download_media(
                fl_data.file_id,
                in_memory=True, progress=progress,
                file_name=f'{settings.download.download_dir}{add_id}'
            )
        elif message:
            file_data = await message.download(
                file_name=f'{settings.download.download_dir}{add_id}',
                in_memory=True, progress=progress
            )
        else:
            file_data = None

        if not os.path.isfile(
                f'{settings.download.download_dir}{add_id}{info_name}'
        ):
            create_dirname(f'{settings.download.download_dir}{add_id}{info_name}')
            try:
                with open(f'{settings.download.download_dir}{add_id}{info_name}', 'w') as iw:
                    iw.write('')
            except:
                log_stack.error(
                    f'{info_name=}, {add_id=},\n'
                    f'{settings.download.download_dir}'
                )

        if not file_data:
            return files

        fl_magic = FileUtils(file_data)
        # logger.info(f'{fl_data.tg_size=} VS {fl_magic.file_size(in_bytes=True)}')
        if fl_data.tg_size and fl_data.tg_size != fl_magic.file_size(in_bytes=True):
            logger.info(f'mismatch size')
            if message:
                await message.forward(
                    chat_id=settings.download.fail_chat_id,
                    disable_notification=True,
                )
            elif client:
                await client.send_message(
                    chat_id=settings.download.stuff_chat_id,
                    text=f'{fl_data}\n',
                    disable_notification=True,
                )

            return files

        fl_magic.md5sum()
        file_path = f'{settings.download.download_dir}{add_id}' \
                    f'{fl_magic.md5}_{file_data.name}'

        new_fl = namedtuple(
            'new_fl', (
                'file_data', 'file_path', 'file_dir', 'saved', 'main_id', 'unique_id',
                'fl_class', 'md5', 'file_size', 'tg_size', 'force_update',
                'db_keys',
                *FL_EFIELDS[file_type]['db_keys'],
                *(x for x in _att if x != 'tp'),
            )
        )
        files.append(
            new_fl._make((
                file_data, file_path,
                f'{settings.download.download_dir}{add_id}',
                False,
                FL_EFIELDS[file_type]['main_id'],
                FL_EFIELDS[file_type]['unique_id'],
                fl_class, fl_magic.md5, fl_magic.file_size(in_bytes=True),
                fl_data.tg_size, force_update,
                (
                    *FL_EFIELDS[file_type]['db_keys'],
                    *(x for x in _att if x != 'tp'),
                ),
                *(getattr(fl_data, x) for x in FL_EFIELDS[file_type]['db_keys']),
                *(getattr(fl_data, x) for x in _att if x != 'tp'),
            ))
        )

        return files

    async def load_discussion_forward(self, enable=[]):

        for enable_name in [
            *settings.discussion.forward.enable,
            *enable
        ]:
            try:
                fwd_data = getattr(
                    settings.discussion.forward, enable_name
                )
            except:
                fwd_data = None

            if fwd_data and fwd_data.enable:
                self.discussion_fwd_data[
                    fwd_data.from_chat_id
                ] = fwd_data

        logger.info(f'{self.discussion_fwd_data=}')

    async def get_to_reply(
            self, what, event, from_reply_id, to_who,
    ):
        to_reply_id = None
        count = 0
        while True:
            from_message = self.db.select(
                'message',
                event.chat.id,
                id=from_reply_id,
            )
            if not from_message:

                if count >= 50:
                    logger.info(f'w fm, {event.chat.id=}, {from_reply_id=},'
                                f' {event.id}')
                    # count = 0
                    check_msg = await self.get_messages(
                        event.chat.id, [from_reply_id, ]
                    )
                    if not check_msg or check_msg[0].empty or check_msg[0].service:
                        break

                if count >= 100:
                    logger.info(f'100 break, {event.chat.id=}, {from_reply_id=},'
                                f' {event.id}')
                    break

                count += 1
                await asyncio.sleep(0.1)
                continue

            if from_message and from_message.service:
                break

            db_search_reply = self.db.select(
                'ForwardedToDiscuss',
                {
                    'from_message': from_message,
                }
            )
            if not db_search_reply:
                if from_message.media_group_id:
                    _f_media_messages = await self.get_media_group_db(
                        event.chat.id,
                        from_reply_id
                    )
                    for _f_media_message in _f_media_messages:

                        db_search_reply = self.db.select(
                            'ForwardedToDiscuss',
                            {
                                'from_message': _f_media_message,
                            }
                        )
                        if db_search_reply:
                            break

            if count >= 100:
                logger.info(f'{from_reply_id=}, '
                            f'{from_message.id if from_message else None}, '
                            f'{from_message=}, {db_search_reply=}')
                break

            count += 1

            # if not db_search_reply:
            #     db_search_reply = self.db.select(
            #         'ForwardedToDiscuss',
            #         {
            #             'event_message': from_message,
            #         }
            #     )

            if db_search_reply:
                to_who = from_message.from_user
                if what and what == 'to_who':
                    return None, to_who

                if db_search_reply.message.media_group_id:

                    logger.info(f'to_reply_group: {db_search_reply=}')
                    msg_group = await self.get_media_group_db(
                        db_search_reply.message.chat.id,
                        db_search_reply.message.id,
                    )

                    if msg_group:
                        to_reply_id = msg_group[0].id
                    else:
                        to_reply_id = db_search_reply.message.id
                else:
                    to_reply_id = db_search_reply.message.id

                break

            await asyncio.sleep(0.1)

        return to_reply_id, to_who

    async def get_post_comment(
            self,
            event: PyrogramMessage,
            data,
            from_who=None,
            to_who=None,
    ):

        sender_chat = None

        if not from_who:
            from_who = getattr(
                event, 'sender_chat'
            ) if event.sender_chat else getattr(
                event, 'from_user'
            ) if event.from_user else None

        if data.peer:
            comment_from = f'c/{data.peer}'
        elif data.username:
            comment_from = f'{data.username}'
        else:
            comment_from = f'c/{event.chat.id}'

        if event.chat.type == pyrogram.enums.ChatType.CHANNEL:
            comment = f'{event.id}'
        else:
            # logger.info(f'{event.reply_to_top_message_id=},'
            #             f'{event.reply_to_message_id=}')
            if event.reply_to_top_message_id:
                msg_id = event.reply_to_top_message_id
            elif event.reply_to_message_id:
                msg_id = event.reply_to_message_id
            else:
                msg_id = event.id

            # logger.info(f'{event.chat.id=}, {msg_id=}\n')
            db_channel_message = None
            event: PyrogramMessage

            if (
                    event.chat.type != pyrogram.enums.ChatType.CHANNEL
            ):
            # ) and (
            #         event.sender_chat
            # ) and (
            #         (
            #                 event.sender_chat.type == pyrogram.enums.ChatType.CHANNEL
            #         ) or (
            #                 event.sender_chat.type == ''
            #         ) or (
            #                 event.sender_chat.type == pyrogram.enums.ChatType.
            #         )
            # ):

                _media_group = []
                db_msg = None

                logger.info(f'{event.id=}, {msg_id=}')
                if event.id != msg_id:
                    db_msg = self.db.select(
                        'message',
                        event.chat.id,
                        id=msg_id
                    )
                    logger.info(f'11:{db_msg=}')
                    if db_msg:
                        if db_msg.media_group_id:
                            _media_group = await self.get_media_group_db(
                                event.chat.id,
                                msg_id,
                            )
                            logger.info(f'{_media_group=}')
                    else:
                        _media_group = await self.get_media_group_db(
                            event.chat.id,
                            msg_id, net=True,
                        )
                else:
                    if event.media_group_id:
                        _media_group = await self.get_media_group_db(
                            event.chat.id,
                            event.id,
                        )

                count = 0
                while True:

                    db_group = []
                    if _media_group:
                        db_group.extend(_media_group)
                    else:
                        if not db_msg:
                            db_msg = self.db.select(
                                'message',
                                event.chat.id,
                                id=msg_id,
                            )

                        if db_msg:
                            db_group.append(db_msg)

                    db_group.sort(key=lambda x: x.id, reverse=False)

                    for db_message in db_group:
                        if not sender_chat:
                            sender_chat = db_message.sender_chat
                            print(f's.2 {sender_chat=}')

                        db_channel_message = self.db.select(
                            '_message',
                            {
                                'discuss_message': db_message,
                            },
                        )
                        if db_channel_message:
                            break

                    if not sender_chat:
                        logger.info(f'no_sender_chat')
                        break

                    #
                    if count >= 100:
                        logger.info(f'{[x.id for x in db_group if x]=}, '
                                    f'{event.media_group_id=}, {db_group=}')
                        count = 0
                        try:
                            reply = None
                            while True:
                                try:
                                    async for reply in self.get_discussion_replies(
                                        chat_id=db_group[0].chat.id,
                                        message_id=db_group[0].id,
                                        limit=1
                                    ):
                                        pass
                                    break
                                except Exception as exc:
                                    break

                            logger.info(f'{reply=}')
                            if reply:
                                try:
                                    messages = await self.get_messages(
                                        db_group[0].forward_from_chat.id,
                                        message_ids=[db_group[0].forward_from_message_id, ]
                                    )
                                    logger.info(f'{messages=}')
                                    db_try = await self.database_message(
                                        message=messages[0]
                                    )
                                    logger.info(f'{db_try=}')
                                except Exception as exc:
                                    log_stack.error('t')
                                    break
                            else:
                                break
                        except:
                            break

                    count += 1

                    # for db_msg in db_group:

                    # if not event.forward_from_message_id:
                    #     # logger.info(f'123TTTTT')
                    #     if not db_channel_message:
                    #         break

                    if db_channel_message:
                        break

                    await asyncio.sleep(0.1)

                # logger.info(f'{db_channel_message=}')

            if db_channel_message:
                if sender_chat:
                    comment_from = f'{sender_chat.username}'
                else:
                    if from_who:
                        comment_from = f'{from_who.username}'

                comment = f'{db_channel_message.id}' \
                          f'?comment={event.id}'
            else:

                comment = f'{event.id}'
                if data.peer:
                    comment_from = f'c/{data.peer}'
                elif data.username:
                    comment_from = f'{data.username}'
                else:
                    comment_from = f'c/{event.chat.id}'

        from_name = f'{from_who.title if hasattr(from_who, "title") and from_who.title else ""}' + \
                    f'{from_who.first_name+" " if hasattr(from_who, "first_name") and from_who.first_name else ""}' \
                    f'{from_who.last_name+" " if hasattr(from_who, "last_name") and from_who.last_name else ""}'
        if to_who:
            to_name = f'{to_who.title if hasattr(to_who, "title") and to_who.title else ""}' + \
                    f'{to_who.first_name+" " if hasattr(to_who, "first_name") and to_who.first_name else ""}' \
                    f'{to_who.last_name+" " if hasattr(to_who, "last_name") and to_who.last_name else ""}'
        else:
            to_name = ''

        if hasattr(data, 'private') and data.private:
            post_text = f'{from_name}\n'

        else:
            post_text = f'{from_name}' \
                        f'{" @" if not to_who and from_who.username else ""}' \
                        f'{from_who.username+" " if not to_who and from_who.username else ""}' \
                        f'{f" --> "+to_name if to_name else ""}' \
                        f'{" @"+to_who.username if to_who and to_who.username else ""}' \
                        f'\n' \
                        f'https://t.me/{comment_from}/{comment}'

        if hasattr(data, 'post_text') and data.post_text:
            post_text += f'\n{data.post_text}'

        return post_text, from_name, to_name
