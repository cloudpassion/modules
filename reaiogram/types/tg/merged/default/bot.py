from .default import AbstractMergedTelegram

from reaiogram.django_telegram.django_telegram.datamanager.tg.bot import (
    BOT_KEYS, BOT_SELECT_KEYS, BOT_HASH_KEY, TgBot
)


class AbstractMergedBot(
    AbstractMergedTelegram
):

    hash_key = BOT_HASH_KEY
    db_keys = BOT_KEYS
    select_keys = BOT_SELECT_KEYS
    db_class = TgBot

