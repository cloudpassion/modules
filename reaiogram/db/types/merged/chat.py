from .default import AbstractMergedTelegram

from ....django_telegram.django_telegram.datamanager.tg.chat import (
    CHAT_KEYS, CHAT_SELECT_KEYS, CHAT_HASH_KEY
)

from ..aiogram.types import AiogramUser


class AbstractMergedChat(
    AbstractMergedTelegram
):

    hash_key = CHAT_HASH_KEY
    db_keys = CHAT_KEYS
    select_keys = CHAT_SELECT_KEYS
