from ..default import TimeBasedModel, models
from .chat import Chat
from .stuff import Poll
from .user import User


class AbstractMessage(TimeBasedModel):
    class Meta:
        abstract = True

    num = models.BigAutoField(primary_key=True)

    id = models.BigIntegerField()

    chat = models.ForeignKey(
        Chat, null=False, on_delete=models.CASCADE,
    )

    date = models.BigIntegerField(null=True)

    db_date = models.BigIntegerField(null=True)
    edit_date = models.BigIntegerField(null=True)
    forward_date = models.BigIntegerField(null=True)

    text = models.TextField(max_length=8196, null=True)
    caption = models.TextField(max_length=1024, null=True)

    from_user = models.ForeignKey(
        User, unique=False, null=True,
        on_delete=models.CASCADE
    )
    from_id = models.BigIntegerField(null=True)

    reply_to_top_message_id = models.BigIntegerField(default=None, null=True)
    reply_to_message_id = models.BigIntegerField(default=None, null=True)
    forward_from_message_id = models.BigIntegerField(default=None, null=True)

    media_group_id = models.BigIntegerField(default=None, null=True)
    media_group_ids = models.TextField(max_length=4096, null=True)

    media_ids = models.TextField(max_length=4096, null=True)

    poll = models.ForeignKey(
        Poll, unique=False, null=True,
        on_delete=models.CASCADE
    )

    reactions = models.TextField(max_length=1024, null=True)
    service = models.TextField(max_length=1024, null=True)
    views = models.BigIntegerField(default=None, null=True)
    entities = models.TextField(max_length=4096, null=True)

    discuss_message = models.ForeignKey(
        'Message', unique=False, null=True,
        on_delete=models.DO_NOTHING,
    )

    hash = models.CharField(max_length=1024, null=False, unique=True)


class Message(AbstractMessage):
    deleted = models.BooleanField(default=False, null=True)

    sender_chat = models.ForeignKey(
        Chat, null=True, on_delete=models.CASCADE,
        related_name='message_sender_chat'
    )
    forward_from_chat = models.ForeignKey(
        Chat, null=True, on_delete=models.CASCADE,
        related_name='message_forward_from_chat'
    )
    forward_from = models.ForeignKey(
        User, null=True, on_delete=models.CASCADE,
        related_name='message_forward_from'
    )


class MessageHistory(AbstractMessage):
    sender_chat = models.ForeignKey(
        Chat, null=True, on_delete=models.CASCADE,
        related_name='history_message_sender_chat'
    )
    forward_from_chat = models.ForeignKey(
        Chat, null=True, on_delete=models.CASCADE,
        related_name='history_message_forward_from_chat'
    )
    forward_from = models.ForeignKey(
        User, null=True, on_delete=models.CASCADE,
        related_name='history_message_forward_from'
    )


# class MessageData(TimeBasedModel):
#
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name_plural = 'MessagesData'
#
#     num = models.BigAutoField(primary_key=True)
#
#     media_group_id = models.BigIntegerField(unique=True, null=False)
#
#     message_ids = models.TextField(max_length=4096, null=True)


__all__ = [
    'Message', 'MessageHistory',

]
