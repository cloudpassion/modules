import pyrogram
import asyncio

import ujson as json

from pyrogram import utils
from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage

from ...client import MyAbstractTelegramClient
from ...db.types.message import MyEventMessageDatabase

from atiny.data import chunks


from ...django_telegram.django_telegram.datamanager.models import (
    Poll as DjangoTelegramPoll,
    Chat as DjangoTelegramChat,
    Message as DjangoTelegramMessage,
    MessageHistory as DjangoTelegramMessageHistory,
    ForwardedToDiscuss,
)

from config import settings
from log import logger, log_stack


class MyPyrogramDbRefactor(
    MyAbstractTelegramClient,
    PyrogramClient
):

    async def db_delete_temp(self):
        chat = DjangoTelegramChat.objects.filter(num=4).first()

        delete_ids = []

        reply_id = 1086

        # data = ForwardedToDiscuss.objects.filter(from_chat=chat).all()
        data = DjangoTelegramMessage.objects.filter(
            chat=chat, reply_to_message_id=reply_id
        ).all()
        for msg in data:
            delete_ids.append(msg.id)

        async for message in self.get_chat_history(
                chat.id,
        ):
            if message.reply_to_message_id == reply_id:
                delete_ids.append(message.id)

            if message.reply_to_top_message_id == reply_id:
                delete_ids.append(message.id)

        logger.info(f'{len(set(delete_ids))=}, {set(delete_ids)=}')
        for chunk in chunks(delete_ids, 200):
            await self.delete_messages(
                chat.id, message_ids=chunk,
            )

    async def db_delete_unexist(self, chat_id=None):

        if chat_id:
            chat = DjangoTelegramChat.objects.filter(id=chat_id).first()
            search = {
                'chat': chat
            }
        else:
            search = {}

        messages = DjangoTelegramMessage.objects.filter(
            **search
        ).all()

        data_to_check = {}
        for db_msg in messages:
            data_to_check[db_msg.chat.id] = []

        for db_msg in messages:
            data_to_check[db_msg.chat.id].append(db_msg.id)
            media_group_ids = json.loads(
                db_msg.media_group_ids
            ) if db_msg.media_group_ids else []

            data_to_check[db_msg.chat.id].extend(
                    media_group_ids
            )

        check_msg = {}
        for g_id, data in data_to_check.items():
            for chunk in chunks(data, 200):

                logger.info(f'{chunk=}, {len(chunk)=}')
                check_msg.update({
                    f'{g_id}_{x.id}': x for x in (
                        await self.get_messages(
                            g_id,
                            message_ids=chunk,
                        )
                    )
                })

        to_delete_db = []
        for db_msg in messages:

            if db_msg.discuss_message:
                key = f'{db_msg.discuss_message.chat.id}_{db_msg.discuss_message.id}'
                check_data = check_msg.get(key)
                if check_data and not check_data.empty:
                    pass
                else:
                    to_delete_db.append(db_msg.discuss_message)

            key = f'{db_msg.chat.id}_{db_msg.id}'
            check_data = check_msg.get(key)
            if check_data and not check_data.empty:
                pass
            else:
                to_delete_db.append(db_msg)

        logger.info(f'{len(to_delete_db)=}')
        to_delete = []
        for db_msg in to_delete_db:

            logger.info(f'del: {db_msg=}, {db_msg.id=}')
            to_delete.extend(
                DjangoTelegramMessageHistory.objects.filter(
                    chat=db_msg.chat, id=db_msg.id,
                ).all()
            )
            to_delete.extend(
                DjangoTelegramMessageHistory.objects.filter(
                    discuss_message=db_msg
                ).all()
            )
            to_delete.extend(
                ForwardedToDiscuss.objects.filter(
                    from_message=db_msg
                ).all()
            )
            to_delete.extend(
                ForwardedToDiscuss.objects.filter(
                    event_message=db_msg
                ).all()
            )
            to_delete.extend(
                DjangoTelegramMessage.objects.filter(
                    discuss_message=db_msg
                ).all()
            )

            to_delete.append(db_msg)

        bad = []
        for x in to_delete:
            try:
                logger.info(f'del2: {x=}, {x.id=}')
            except:
                try:
                    logger.info(f'del3: {x=}, {x.message.id=}')
                except:
                    logger.info(f'del4: {x=}')

            # try:
            #     x.delete()
            # except:
            #     bad.append(x)

        for x in bad:
            logger.info(f'{x=}')


