from ...django.tg.update import DjangoORMTgUpdate
from ...django.tg.bot import DjangoORMTgBot

from ...django.tg.user import DjangoORMTgUser
from ...django.tg.chat import DjangoORMTgChat
from ...django.tg.message import DjangoORMTgMessage

from ...django.tg.file import DjangoORMTgFiles

from log import logger

from ....types.tg.message import MergedTelegramMessage
from ....types.tg.update import MergedTelegramUpdate
from ....types.tg.bot import MergedTelegramBot

from ...exceptions import DbBreakException


class MyDjangoTgORM(

    DjangoORMTgBot,
    DjangoORMTgUpdate,

    DjangoORMTgChat,
    DjangoORMTgUser,
    DjangoORMTgMessage,

    DjangoORMTgFiles,
):

    async def database_default(
            self,
            key,
            data,
            **kwargs
    ):
        try:
            if key == 'bot':
                return await self._database_default(
                    value=data, merge_class=MergedTelegramBot, merge_func_key=key
                )
            if key == 'update':
                return await self._database_default(
                    value=data,
                    merge_class=MergedTelegramUpdate, merge_func_key=key,
                    **kwargs,
                )
            if key == 'message':
                return await self._database_default(
                    value=data, merge_class=MergedTelegramMessage, merge_func_key=key
                )
        except DbBreakException:
            return {}
        except Exception:
            quit()
            return 'stack'

    async def database_bot(
            self,
            bot,
    ):
        return await self.database_default('bot', bot)

    async def database_update(
            self,
            update,
            merged_bot,
    ):
        return await self.database_default('update', update, merged_bot=merged_bot)

    async def database_message(
            self,
            message,
    ):
        return await self.database_default('message', message)

    async def _database_default(
            self,
            value,
            merge_class,
            merge_func_key,
            **kwargs,
    ):
        if not value:
            return f'no_data {merge_class}'

        data = {}
        merge_kwargs = {
            merge_func_key: value,
            **kwargs,
        }

        # merge message from pyrogram and aiogram to one format
        new_data = merge_class(self, **merge_kwargs)
        merge_func = getattr(new_data, f'merge_{merge_func_key}')
        await merge_func()

        data[f'merged_{merge_func_key}'] = new_data

        await new_data._convert_to_orm()

        return data
