from ..default import ExtraBasedModel, models


UPDATE_KEYS = (
    'bot',
    'id',
    'message',
    'edited_message',
    'channel_post',
    'edited_channel_post',
    'inline_query',
    'chosen_inline_result',
    'callback_query',
    'shipping_query',
    'pre_checkout_query',
    'poll',
    'poll_answer',
    'my_chat_member',
    'chat_member',
    'chat_join_request',
)

UPDATE_SELECT_KEYS = ('bot', 'id', )
UPDATE_HASH_KEY = 'update'


class AbstractTgUpdate(ExtraBasedModel):
    class Meta:
        abstract = True

    db_keys = UPDATE_KEYS
    select_keys = UPDATE_SELECT_KEYS
    hash_key = UPDATE_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    bot = models.ForeignKey(
        'TgBot',
        on_delete=models.DO_NOTHING,
        null=False,
    )

    message = models.ForeignKey(
        'TgMessage',
        on_delete=models.DO_NOTHING,
        related_name='update_message',
        null=True, blank=True,
    )

    edited_message = models.ForeignKey(
        'TgMessage',
        on_delete=models.DO_NOTHING,
        related_name='update_edited_message',
        null=True, blank=True,
    )
    channel_post = models.ForeignKey(
        'TgMessage',
        on_delete=models.DO_NOTHING,
        related_name='update_channel_post',
        null=True, blank=True,
    )
    edited_channel_post = models.ForeignKey(
        'TgMessage',
        on_delete=models.DO_NOTHING,
        related_name='update_edited_channel_post',
        null=True, blank=True,
    )
    # 'inline_query',
    # 'chosen_inline_result',
    # 'callback_query',
    # 'shipping_query',
    # 'pre_checkout_query',
    # 'poll',
    # 'poll_answer',
    # 'my_chat_member',
    # 'chat_member',
    # 'chat_join_request',


class TgUpdate(AbstractTgUpdate):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgUpdate'

    id = models.BigIntegerField(
        unique=False, verbose_name="Update ID")


__all__ = ['TgUpdate', ]
