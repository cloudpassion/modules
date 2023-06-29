from ...django.tg.update import DjangoORMTgUpdate
from ...django.tg.bot import DjangoORMTgBot

from ...django.tg.user import DjangoORMTgUser
from ...django.tg.chat import DjangoORMTgChat
from ...django.tg.message import DjangoORMTgMessage

from ...django.tg.file import DjangoORMTgFiles

from log import logger, log_stack

from ....types.tg.message import MergedTelegramMessage
from ....types.tg.update import MergedTelegramUpdate
from ....types.tg.bot import MergedTelegramBot

from ...exceptions import DbBreakException
from ....utils.enums import UPDATE_TYPES


MERGED_CL = {
    'message': MergedTelegramMessage,
    'bot': MergedTelegramBot,
    'update': MergedTelegramUpdate,
}


class MyDjangoTgORM(

    DjangoORMTgBot,
    DjangoORMTgUpdate,

    DjangoORMTgChat,
    DjangoORMTgUser,
    DjangoORMTgMessage,

    DjangoORMTgFiles,
):
    async def bot_to_orm(self, bot):
        return await self.data_to_orm(bot=bot)

    async def update_to_orm(self, update, merged_bot, **kwargs):
        return await self.data_to_orm(update=update, merged_bot=merged_bot, **kwargs)

    async def message_to_orm(self, message, **kwargs):
        return await self.data_to_orm(message=message, **kwargs)

    async def data_to_orm(
            self,
            **kwargs
    ):
        try:
            return await self._data_to_orm(
                **kwargs,
            )
        except DbBreakException:
            return {}
        except Exception:
            log_stack.error(f'{kwargs=}')
            quit()
            return 'stack'

    async def _data_to_orm(
            self,
            prefix='',
            **kwargs,
    ):
        key = list(kwargs)[0]

        if not key:
            return {}

        data = {}
        merge_class = MERGED_CL[key]
        merge_kwargs = {
            **kwargs,
        }

        # logger.info(f'{key=}, {merge_class=}')

        # merge message from pyrogram and aiogram to one format
        new_data = merge_class(orm=self, **merge_kwargs)

        merge_func = getattr(new_data, f'merge_{key}')
        # logger.info(f'before merge {new_data=}')
        await merge_func()
        # logger.info(f'after merge {new_data=}')
        # convert_func = getattr(new_data, f'_convert_to_orm')
        # await new_data._convert_to_orm('new_database')
        # logger.info(f'after orm')

        if key == 'update':
            data.update({
                **{
                    f'merged_{u}': getattr(new_data, u) for u in UPDATE_TYPES
                }
            })
        else:
            data[f'{f"{prefix}_" if prefix else ""}merged_{key}'] = new_data

        return data
