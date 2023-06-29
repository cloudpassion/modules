from .default import AbstractMergedTelegram

from reaiogram.django_telegram.django_telegram.datamanager.tg.message import (
    MESSAGE_KEYS, MESSAGE_SELECT_KEYS, MESSAGE_HASH_KEY, TgMessage
)


class AbstractMergedMessage(
    AbstractMergedTelegram
):

    hash_key = MESSAGE_HASH_KEY
    db_keys = MESSAGE_KEYS
    select_keys = MESSAGE_SELECT_KEYS
    db_class = TgMessage

