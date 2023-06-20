from ....django_telegram.django_telegram.datamanager.models import (
    Chat
)
from asgiref.sync import sync_to_async

from log import log_stack, mlog

from .default import DefaultDjangoORM


class DjangoChatORM(DefaultDjangoORM):

    @staticmethod
    @sync_to_async
    def select_chat(chat_id: int):
        try:
            chat = Chat.objects.filter(chat_id=chat_id).first()
        except:
            log_stack.error(f'select: {chat_id=}')

        mlog.info(f'select: {chat=}')

        if not chat:
            return Chat(chat_id=int(chat_id)).save()

        return chat

    @sync_to_async
    def add_chat(
            self, chat_id, title, full_name, username
    ):
        try:
            return User(user_id=int(user_id), name=full_name, username=username).save()
        except django.db.utils.IntegrityError:
            # duplicate key value violates unique constraint "usersmanage_user_user_id_key"
            return User.objects.filter(user_id=user_id).first()
        except Exception:
            log_stack.info(f'except {user_id=}, {full_name=}, {username=}')

    @staticmethod
    @sync_to_async
    def select_all_chats():
        chats = Chat.objects.all()
        return chats

    @staticmethod
    @sync_to_async
    def count_chats():
        return Chat.objects.all().count()
