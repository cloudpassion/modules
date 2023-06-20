from ..default import ExtraBasedModel, models
from .message import TgMessage
from .chat import TgChat


class ForwardedToDiscuss(ExtraBasedModel):
    class Meta:
        app_label = 'datamanager'

    num = models.BigAutoField(primary_key=True)

    hint = models.TextField(max_length=8196, null=True)

    chat = models.ForeignKey(
        TgChat, on_delete=models.DO_NOTHING,
        related_name='forwarded_to_discuss_chat'
    )
    message = models.ForeignKey(
        TgMessage, on_delete=models.DO_NOTHING,
        related_name='forwarded_to_discuss_message'
    )

    from_chat = models.ForeignKey(
        TgChat, on_delete=models.DO_NOTHING,
        related_name='forwarded_to_discuss_from_chat'
    )
    from_message = models.ForeignKey(
        TgMessage, on_delete=models.DO_NOTHING,
        related_name='forwarded_to_discuss_from_message'
    )

    event_message = models.ForeignKey(
        TgMessage, on_delete=models.DO_NOTHING,
        related_name='forwarded_to_discuss_event_message'
    )
    date = models.BigIntegerField(null=True)
    edit_date = models.BigIntegerField(null=True)

    group_ids = models.TextField(max_length=4096, null=True)
    post_text = models.TextField(max_length=8196, null=True)

    deleted = models.BooleanField(null=True)


__all__ = [
    'ForwardedToDiscuss',
]
