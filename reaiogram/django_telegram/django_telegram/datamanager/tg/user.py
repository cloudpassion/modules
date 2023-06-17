from ..default import ExtraBasedModel, models


USER_KEYS = (
    'id',
    'is_bot',
    'first_name',
    'last_name',
    'username',
    'language_code',
    'is_premium',
    'added_to_attachment_menu',
    # getMe
    'can_join_groups',
    'can_read_all_group_messages',
    'supports_inline_queries',
)

USER_SELECT_KEYS = ('id', )
USER_HASH_KEY = 'user'


class AbstractTgUser(ExtraBasedModel):
    class Meta:
        abstract = True

    db_keys = USER_KEYS
    select_keys = USER_SELECT_KEYS
    hash_key = USER_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    is_bot = models.BooleanField(null=False, blank=True)
    first_name = models.CharField(max_length=128, null=False)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    username = models.CharField(max_length=128, null=True, blank=True)
    language_code = models.CharField(max_length=2, null=True, blank=True)
    is_premium = models.BooleanField(null=True, blank=True)
    added_to_attachment_menu = models.BooleanField(null=True, blank=True)

    # getMe
    can_join_groups = models.BooleanField(null=True, blank=True)
    can_read_all_group_messages = models.BooleanField(null=True, blank=True)
    supports_inline_queries = models.BooleanField(null=True, blank=True)


class TgUser(AbstractTgUser):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgUser'

    id = models.BigIntegerField(
        unique=True, verbose_name="Telegram User ID"
    )

    deleted = models.BooleanField(
        default=False,
        null=True, blank=True
    )


class TgUserHistory(AbstractTgUser):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgUsers History'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram User ID"
    )


__all__ = [
    'TgUser', 'TgUserHistory',
]
