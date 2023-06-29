from .default import AbstractMergedTelegram

from reaiogram.django_telegram.django_telegram.datamanager.tg.update import (
    UPDATE_KEYS, UPDATE_SELECT_KEYS, UPDATE_HASH_KEY, TgUpdate
)


class AbstractMergedUpdate(
    AbstractMergedTelegram
):

    hash_key = UPDATE_HASH_KEY
    db_keys = UPDATE_KEYS
    select_keys = UPDATE_SELECT_KEYS

    db_class = TgUpdate
