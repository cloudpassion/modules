import pyrogram.enums
import ujson as json

from ...client import MyAbstractTelegramClient
from pyrogram.types import Message, List
from pyrogram.errors.exceptions.flood_420 import FloodWait

from config import settings
from log import logger, log_stack


class MyTelegramParseMedia(
    MyAbstractTelegramClient
):

    media_func = {
        'photo': 'parse_photo',
        'video': 'parse_video',
        'audio': 'parse_audio',
        'voice': 'parse_voice',
        'sticker': 'parse_sticker',
        'document': 'parse_document',
    }

    media_class = {
        'photo': pyrogram.enums.MessageMediaType.PHOTO,
        'document': pyrogram.enums.MessageMediaType.DOCUMENT,
        'video': pyrogram.enums.MessageMediaType.VIDEO,
        'audio': pyrogram.enums.MessageMediaType.AUDIO,
        'voice': pyrogram.enums.MessageMediaType.VOICE,
        'sticker': pyrogram.enums.MessageMediaType.STICKER,
    }

    async def parse_files(
            self, message,
    ):
        files = []
        for _tp in self.media_func.keys():
            if hasattr(message, _tp) and getattr(message, _tp):

                if getattr(settings.download, 'all'):
                    pass
                else:
                    if not getattr(settings.download, _tp):
                        continue

                if getattr(message, 'media_group_id'):
                    setattr(
                        getattr(message, _tp), 'media_group_id',
                        message.media_group_id
                    )
                else:
                    setattr(
                        getattr(message, _tp), 'media_group_id', None
                    )

                _add = await getattr(
                    self, self.media_func[_tp]
                )(
                    message,
                )
                if _add:
                    files.extend(_add)

        return files

    async def default_parse(
            self, tp, message,
    ):
        files = []
        doc = getattr(message, tp)
        doc.tg_size = doc.file_size
        if hasattr(message, tp) and getattr(message, tp):
            doc.tp = tp
        else:
            return []

        fl = await self.download_file(
            fl_data=doc, client=self, message=message,
            add_id=message.chat.add_id, info_name=message.chat.info_name
        )
        files.extend(fl)
        fl = await self.parse_thumbs(
            tp=tp, message=message,
            fl=fl[0]
        )
        files.extend(fl)

        return files

    async def parse_thumbs(
            self, tp, message, fl,
    ):
        files = []

        media = getattr(message, tp)
        thumbs = getattr(media, 'thumbs') if hasattr(media, 'thumbs') else None
        if not thumbs:
            return files

        if tp == 'sticker':
            setattr(
                message.chat, 'add_id',
                f'/stickers/{message.sticker.set_name}/'
            )

        for thumb in thumbs:

            thumb.tg_size = thumb.file_size
            thumb.tp = 'thumb'
            thumb.tag = f'thumb_{tp}'
            thumb.fl_md5 = fl.md5

            result = await self.download_file(
                fl_data=thumb, client=self, message=message,
                add_id=message.chat.add_id, info_name=message.chat.info_name,
                _att=['tag', 'fl_md5']
            )
            files.extend(result)

        return files

    async def parse_sticker(
            self, message: Message,
    ):
        return await self.default_parse('sticker', message)

    async def parse_document(
            self, message: Message,
    ):
        return await self.default_parse('document', message)

    async def parse_video(
            self, message: Message,
    ):
        return await self.default_parse('video', message)

    async def parse_audio(
            self, message: Message
    ):
        return await self.default_parse('audio', message)

    async def parse_voice(
            self, message: Message
    ):
        return await self.default_parse('voice', message)

    async def parse_photo(
            self, message: Message
    ):
        return await self.default_parse('photo', message)

    async def get_media_group_db(
            self,
            chat_id, message_id=None, media_group_id=None,
            net=False, cache=True,
    ):

        media_group_ids = []
        if message_id:
            db_msg = self.db.select(
                'message',
                chat_id,
                id=message_id,
            )
            if db_msg:
                media_group_ids = json.loads(
                    db_msg.media_group_ids
                ) if db_msg.media_group_ids else []
                media_group_id = db_msg.media_group_id

        elif media_group_id:
            db_group = self.db.select_all(
                '_message',
                chat_id,
                media_group_id=media_group_id
            )
            if db_group:
                for db_msg in db_group:
                    _media_group_ids = json.loads(
                        db_msg.media_group_ids
                    ) if db_msg.media_group_ids else []
                    if _media_group_ids:
                        media_group_ids = _media_group_ids
                        message_id = media_group_ids[0]
                        break

        media_group_ids.sort(key=lambda x: x, reverse=False)
        msg_group = []
        if media_group_ids:
            for msg_id in media_group_ids:
                db_msg = self.db.select(
                    'message',
                    chat_id,
                    id=msg_id,
                )
                if not db_msg:
                    break

                msg_group.append(db_msg)

        if msg_group and len(msg_group) == len(media_group_ids) and not net:
            msg_group.sort(key=lambda x: x.id, reverse=False)
            return msg_group

        if cache and self.media_group_messages[media_group_id]:
            return self.media_group_messages[media_group_id]

        media_group = []
        while True:
            try:
                logger.info(f'request media for: {chat_id=}, {message_id=}')
                media_group = await self.get_media_group(
                    chat_id,
                    message_id,
                )
                media_group.sort(key=lambda x: x.id, reverse=False)
                self.media_group_messages[
                    media_group[0].media_group_id
                ] = media_group
                break
            except FloodWait as exc:
                await self.parse_flood('get_mdb', exc)
            except Exception:
                break

        return media_group
