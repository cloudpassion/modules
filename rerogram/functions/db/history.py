import pyrogram
import asyncio

from pyrogram import utils
from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage
from pyrogram.errors.exceptions.bad_request_400 import FileReferenceExpired

from ...client import MyAbstractTelegramClient
from ...db.types.message import MyEventMessageDatabase

from config import settings
from log import logger, log_stack


class MyPyrogramDbHistory(
    MyAbstractTelegramClient,
    PyrogramClient
):

    async def db_insert_messages(
            self, chat_id, chats_data={},
            sleep=0, offset_id=0, limit=1, offset=0,
            offset_date=utils.zero_datetime(),
    ):

        while True:
            try:
                logger.info(f'{chat_id=}')
                available_ids = []
                messages = []

                if offset_id and offset_id == 'last':
                    async for message in self.get_chat_history(
                            chat_id, limit=1,
                    ):
                        offset_id = message.id+1
                        # peer = await self.resolve_peer(message.chat.id)
                        # logger.info(f'{message=}')
                        # logger.info(f'{peer=}')

                async for message in self.get_chat_history(
                        chat_id, offset_id=offset_id,
                        limit=limit,
                        # limit=limit if offset_id-limit > 0 else offset_id-1,
                        offset=offset,
                        offset_date=offset_date
                ):
                    available_ids.append(message.id)
                    messages.append(message)

                for message in reversed(messages):

                    await self.database_message(
                        message=message,
                    )

                    # if message.id > min(available_ids) and message.id in available_ids and message.deleted:
                    #     logger.info(f'restore')
                    #     await self.database_message(
                    #         message=message,
                    #     )
                    #

                to_forward = []
                for message in reversed(messages):

                    chat_data = chats_data.get(chat_id)
                    if chat_data and chat_data.get('check_forward'):

                        if message.service:
                            continue

                        to_forward.append(message)

                if chats_data.get(chat_id):
                    edit = await self.discuss_forward_edit(
                        events=to_forward,
                        data=chats_data[chat_id],
                    )
                    for fwd in edit:
                        fwd_db_msg = fwd[0]
                        fwd_event = fwd[1]

                        # logger.info(f'{fwd_db_msg=}')
                        if not fwd_db_msg:
                            logger.info(f'discuss_new')
                            await self.discuss_forward_new(
                                event=fwd_event,
                                data=chats_data[fwd_event.chat.id]
                            )
                            await asyncio.sleep(sleep)

                logger.info(f'END DB:{chat_id=}')

                db = self.db.select_all(
                    'message',
                    chat_id,
                )

                for db_message in db:
                    if not available_ids:
                        continue

                    if db_message.id > min(
                            available_ids
                    ) and db_message.id < max(
                        available_ids
                    ) and db_message.id not in available_ids and not db_message.deleted:
                        logger.info(f'delete: {db_message=}')

                        await self.database_message(
                            message=[db_message, ], delete=True,
                        )
                break
            except FileReferenceExpired:
                log_stack.error(f'flrf')
                await asyncio.sleep(600)
                continue
            except Exception:
                log_stack.error(f'exc')
                break
