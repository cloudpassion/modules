from .default import AbstractMergedTelegram

from ....django_telegram.django_telegram.datamanager.tg.user import (
    USER_KEYS, USER_SELECT_KEYS, USER_HASH_KEY
)

from ..aiogram.types import AiogramUser


class AbstractMergedUser(
    AbstractMergedTelegram
):

    hash_key = USER_HASH_KEY
    db_keys = USER_KEYS
    select_keys = USER_SELECT_KEYS
