import asyncio

from ....db.schemas.django.tg.chat import DjangoORMTgChat
from ....db.schemas.django.tg.user import DjangoORMTgUser
from ....db.schemas.django.tg.message import DjangoORMTgMessage

from ....db.schemas.django.tg.file import DjangoORMTgFiles

from log import logger, log_stack

from ...types.message import MergedTelegramMessage

from ..exceptions import DbBreakException


class MyDjangoORM(
    DjangoORMTgChat,
    DjangoORMTgUser,
    DjangoORMTgMessage,

    DjangoORMTgFiles,
):

    async def database_message(
            self,
            message,
            # MESSAGE_TYPES,
            # delete=False,
            # check=False,
            # _media_messages=None,
    ):
        try:
            return await self._database_message(
                message=message,
                # delete=delete,
                # check=check,
                # _media_messages=_media_messages,
            )
        except DbBreakException:
            return True
        except Exception:
            # log_stack.error(f'stack: {message=}')
            # await asyncio.sleep(10)
            quit()

            return 'stack'

    async def _database_message(
            self,
            message,
            # : MESSAGE_TYPES,
            delete=False,
            # check=False,
            # _media_messages=None,
    ):
        data = {}
        if not message:
            logger.info(f'no message')
            return 'no_message'

        # merge message from pyrogram and aiogram to one format
        message = MergedTelegramMessage(self, message)
        await message.merge_message()

        data['merged_message'] = message

        # at this step add, update or delete message in asdfasdf

        logger.info(f'{message=}')
        logger.info(f'{message.from_user=}')
        # return merged or asdfasdf? message

        await message._convert_to_orm()
        # logger.info(f'{db_values=}')

        return data
