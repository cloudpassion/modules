from ..default import ExtraBasedModel, models
from .chat import TgChat
# from .stuff import Poll
from .user import TgUser


MESSAGE_KEYS = (
    'id',
    'thread_id',
    'from_user',
    'sender_chat',
    'date',
    'chat',
    'forward_from',
    'forward_from_chat',
    'forward_from_message_id',
    'forward_signature',
    'forward_sender_name',
    'forward_date',
    'is_topic_message',
    'is_automatic_forward',
    'reply_to_message',
    'via_bot',
    'edit_date',
    'has_protected_content',
    'media_group_id',
    'author_signature',
    'text',
    'entities',
    'animation',
    'audio',
    'document',
    'photo',
    'sticker',
    'video',
    'video_note',
    'voice',
    'caption',
    'caption_entities',
    'has_media_spoiler',
    'contact',
    'dice',
    'game',
    'poll',
    'venue',
    'location',
    'new_chat_members',
    'left_chat_member',
    'new_chat_title',
    'new_chat_photo',
    'delete_chat_photo',
    'group_chat_created',
    'supergroup_chat_created',
    'channel_chat_created',
    'message_auto_delete_timer_changed',
    'migrate_to_chat_id',
    'migrate_from_chat_id',
    'pinned_message',
    'invoice',
    'successful_payment',
    'user_shared',
    'chat_shared',
    'connected_website',
    'write_access_allowed',
    'passport_data',
    'proximity_alert_triggered',
    'forum_topic_created',
    'forum_topic_edited',
    'forum_topic_closed',
    'forum_topic_reopened',
    'general_forum_topic_hidden',
    'general_forum_topic_unhidden',
    'video_chat_scheduled',
    'video_chat_started',
    'video_chat_ended',
    'video_chat_participants_invited',
    'web_app_data',
    'reply_markup',
)

MESSAGE_SELECT_KEYS = ('chat', 'id')
MESSAGE_HASH_KEY = 'message'


class AbstractTgMessage(ExtraBasedModel):
    class Meta:
        app_label = 'datamanager'
        abstract = True

    db_keys = MESSAGE_KEYS
    select_keys = MESSAGE_SELECT_KEYS
    hash_key = MESSAGE_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    thread_id = models.BigIntegerField(
        verbose_name="Telegram Message ThreadID",
        null=True, blank=True
    )

    from_user = models.ForeignKey(
        TgUser, on_delete=models.CASCADE,
        null=True, blank=True
    )

    # 'sender_chat' in TgMessage
    date = models.BigIntegerField(null=False)

    chat = models.ForeignKey(
        TgChat, on_delete=models.CASCADE,
        null=False,
    )

    # 'forward_from' in TgMessage
    # 'forward_from_chat' in TgMessage

    forward_from_message_id = models.BigIntegerField(
        null=True, blank=True
    )

    # 'forward_signature',
    # 'forward_sender_name',

    forward_date = models.BigIntegerField(null=True, blank=True)

    # 'is_topic_message',
    # 'is_automatic_forward',

    # 'reply_to_message',
    # 'via_bot',
    edit_date = models.BigIntegerField(null=True, blank=True)

    # 'has_protected_content',
    # 'media_group_id',
    # 'author_signature',

    text = models.TextField(max_length=8196, null=True, blank=True)
    # 'entities',
    # 'animation',
    # 'audio',
    document = models.ForeignKey(
        'TgDocument',
        on_delete=models.DO_NOTHING,
        null=True, blank=True,
    )
    # 'photo',
    # 'sticker',
    # 'video',
    # 'video_note',
    # 'voice',
    caption = models.TextField(max_length=8196, null=True, blank=True)
    # 'caption_entities',

    discuss_message = models.ForeignKey(
        'TgMessage',
        on_delete=models.DO_NOTHING,
        null=True, blank=True,
    )


class TgMessage(AbstractTgMessage):

    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgMessage'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram Message ID")

    deleted = models.BooleanField(default=False, null=True)

    sender_chat = models.ForeignKey(
        TgChat, on_delete=models.CASCADE,
        related_name='message_sender_chat',
        null=True, blank=True,
    )
    forward_from_chat = models.ForeignKey(
        TgChat, on_delete=models.CASCADE,
        related_name='message_forward_from_chat',
        null=True, blank=True,
    )
    forward_from = models.ForeignKey(
        TgUser, on_delete=models.CASCADE,
        related_name='message_forward_from',
        null=True, blank=True,
    )


class TgMessageHistory(AbstractTgMessage):

    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgMessage History'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram Message ID")

    sender_chat = models.ForeignKey(
        TgChat, on_delete=models.CASCADE,
        related_name='history_message_sender_chat',
        null=True, blank=True,

    )
    forward_from_chat = models.ForeignKey(
        TgChat, on_delete=models.CASCADE,
        related_name='history_message_forward_from_chat',
        null=True, blank=True,
    )
    forward_from = models.ForeignKey(
        TgUser, on_delete=models.CASCADE,
        related_name='history_message_forward_from',
        null=True, blank=True,
    )


__all__ = [
    'TgMessage', 'TgMessageHistory',
]
