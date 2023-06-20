from ..default import ExtraBasedModel, models


CHAT_KEYS = (
    'id',
    'type',
    'title',
    'username',
    'first_name',
    'last_name',
    # getChat
    'is_forum',
    'photo',
    'active_usernames',
    'emoji_status_custom_emoji_id',
    'bio',
    'has_private_forwards',
    'has_restricted_voice_and_video_messages',
    'join_to_send_messages',
    'join_by_request',
    'description',
    'invite_link',
    'pinned_message',
    'permissions',
    'slow_mode_delay',
    'message_auto_delete_time',
    'has_aggressive_anti_spam_enabled',
    'has_hidden_members',
    'has_protected_content',
    'sticker_set_name',
    'can_set_sticker_set',
    'linked_chat_id',
    'location',
)

CHAT_SELECT_KEYS = ('id', )
CHAT_HASH_KEY = 'chat'


class AbstractTgChat(ExtraBasedModel):
    class Meta:
        abstract = True

    db_keys = CHAT_KEYS
    select_keys = CHAT_SELECT_KEYS
    hash_key = CHAT_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    type = models.CharField(max_length=128, null=False)
    title = models.CharField(max_length=64, null=True, blank=True)
    username = models.CharField(max_length=64, null=True, blank=True)

    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)

    # getChat
    is_forum = models.BooleanField(default=False, null=True, blank=True)
    # date = models.BigIntegerField(null=True)
    # big_file_id
    # photo = models.CharField(max_length=512, null=True)

    # big
    # invite_link = models.CharField(max_length=256, null=True)
    # members_count = models.BigIntegerField(null=True)
    # available_reactions = models.TextField(max_length=1024, null=True)
    # description = models.TextField(max_length=8196, null=True)


class TgChat(AbstractTgChat):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgChat'

    id = models.BigIntegerField(
        unique=True, verbose_name="Telegram Chat ID")


class TgChatHistory(AbstractTgChat):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgChats History'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram Chat ID")


__all__ = ['TgChat', 'TgChatHistory', ]
