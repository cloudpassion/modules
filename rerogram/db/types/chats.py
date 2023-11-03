from typing import Union
import pyrogram.types

from datetime import datetime

from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram import Client as PyrogramClient
from pyrogram.types import (
    User as PyrogramUser, Chat as PyrogramChat,
)
from ...django_telegram.django_telegram.datamanager.models import (
    User as DjangoTelegramUser,
    Chat as DjangoTelegramChat,
)

from pyrogram.raw.types.channel import Channel
from pyrogram.raw.functions.channels.get_full_channel import GetFullChannel
from pyrogram.raw.functions.messages.get_full_chat import GetFullChat

from ...client import MyAbstractTelegramClient

from log import logger, log_stack
from config import settings


class MyChatDatabase(
    MyAbstractTelegramClient,
    PyrogramClient,
):
    db_user: dict
    db_chat: dict
    db_full_chat: dict

    def load_database_data(self):
        self.db_user = {
            PyrogramUser: self._pyrogram_database_user,
            # DjangoTelegramUser: self._django_database_user,
        }
        self.db_chat = {
            PyrogramChat: self._pyrogram_database_chat,
            # DjangoTelegramChat: self._django_database_chat,
        }
        self.db_full_chat = {
            PyrogramChat: self._pyrogram_get_full_chat,
        }

    async def _django_database_user(self, user):
        return await self._pyrogram_database_user(
            await self.get_users([user.id, ])[0]
        )

    async def _pyrogram_database_user(self, user):
        return await self._default_database_user(user)

    def get_info_name(self, user=None, chat=None):
        if user:
            user.info_name = f'{user.first_name if user.first_name else ""}' \
                        f'{" " if user.first_name else ""}' \
                        f'{user.last_name if user.last_name else ""}' \
                        f'{" " if user.last_name else ""}' \
                        f'{"@" if user.username else ""}' \
                        f'{user.username if user.username else ""}'

        if chat:
            chat.info_name = f'{chat.title if chat.title else ""}' \
                        f'{" " if chat.title else ""}' \
                        f'{"@" if chat.username else ""}' \
                        f'{chat.username if chat.username else ""}'

    async def _default_database_user(self, user):

        db_keys = (
            'id', 'first_name', 'last_name', 'username', 'phone_number',
            'photo'
        )
        extra_keys = (
           'photos', 'info_name'
        )

        for k in (*db_keys, *extra_keys):
            if not hasattr(user, k):
                setattr(user, k, None)

        self.get_info_name(user=user)
        user.add_id = f'/{user.id}/'

        if user.photo:
            for k in ('tag', 'tp', 'file_id', 'tg_size'):
                if not hasattr(user.photo, k):
                    setattr(user.photo, k, None)
            user.photo.tag = 'user_photo'
            user.photo.tp = 'user_photo'
            user.photo.file_id = user.photo.big_file_id

            user.photos = await self.download_file(
                fl_data=user.photo, message=None, client=self,
                _att=('tag', 'tp'), add_id=user.add_id,
                info_name=user.info_name,
            )
            user.photo = user.photo.file_id

        add_data = self.db.add_data(
            'user',
            add_id=user.id,
            files=user.photos,
            **{k: getattr(user, k) for k in db_keys},
        )
        return add_data

    async def database_user(
            self,
            message=None,
            user=None,
    ):

        if not user and not message:
            return

        if message and not user:
            try:
                user = message.from_user
            except AttributeError:
                return

        func = self.db_user.get(type(user))
        return await func(user=user)

    async def database_chat(
            self,
            message=None,
            chat=None
    ):

        if not chat and not message:
            return

        if message and not chat:
            try:
                chat = message.chat
            except AttributeError:
                return

        func = self.db_chat.get(type(chat))
        return await func(chat=chat)

    async def _get_full_chat(self, chat, wait=False):
        func = self.db_full_chat.get(type(chat))
        return await func(chat=chat, wait=wait)

    async def _pyrogram_get_full_chat(self, chat, wait=False):

        if not self.chat_data[chat.id].get('full'):
            full = False

            while not full:
                try:
                    full = await self.get_chat(chat_id=chat.id)
                    self.chat_data[chat.id]['full'] = True
                except FloodWait as exc:
                    await self.parse_flood('database_chat_get_full', exc, wait=False)
                    return
                except Exception as exc:
                    try:
                        log_stack.error(f'get full exception, {chat.id=}, {chat=}')
                    except AttributeError:
                        logger.info(f'{chat=}, {exc=}')

                if not wait:
                    break
        else:
            full = self.db.select('chat', chat.id)

        return full

    async def _django_database_chat(self, chat):
        return await self._pyrogram_database_chat(
            chat=(await self.get_chat(chat.id)),
        )

    async def _pyrogram_database_chat(self, chat):

        db_keys = (
            'id', 'title', 'username',
            'photo', 'type',
        )
        full_keys = (
            'invite_link', 'members_count', 'description',
        )
        extra_keys = (
            'photos', 'info_name', 'full'
        )

        for k in (*db_keys, *full_keys, *extra_keys):
            if not hasattr(chat, k):
                setattr(chat, k, None)

        self.get_info_name(chat=chat)
        chat.add_id = f'/{chat.id}/'

        full = await self._get_full_chat(chat=chat, wait=False)

        if full:
            for k in full_keys:
                setattr(chat, k, getattr(full, k))

        if chat.photo:
            for k in ('tag', 'tp', 'file_id', 'tg_size'):
                if not hasattr(chat.photo, k):
                    setattr(chat.photo, k, None)
            chat.photo.tag = 'chat_photo'
            chat.photo.tp = 'chat_photo'
            chat.photo.file_id = chat.photo.big_file_id

            chat.photos = await self.download_file(
                fl_data=chat.photo, message=None, client=self,
                _att=('tag', 'tp'), add_id=chat.add_id,
                info_name=chat.info_name,
            )
            chat.photo = chat.photo.file_id

        add_data = self.db.add_data(
            'chat',
            add_id=chat.id,
            files=chat.photos,
            **{k: getattr(chat, k) for k in (*db_keys, *full_keys)},
        )
        return add_data

