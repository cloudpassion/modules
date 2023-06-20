from ..default import models
from .user import AbstractTgUser, USER_KEYS, USER_SELECT_KEYS

BOT_KEYS = USER_KEYS
BOT_SELECT_KEYS = USER_SELECT_KEYS
BOT_HASH_KEY = 'bot'


class TgBot(AbstractTgUser):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgBot'

    id = models.BigIntegerField(
        unique=True, verbose_name="Telegram Bot ID"
    )

    deleted = models.BooleanField(
        default=False,
        null=True, blank=True
    )


__all__ = ('TgBot', )
