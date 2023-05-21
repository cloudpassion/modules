from ..default import TimeBasedModel, models


class AbstractChat(TimeBasedModel):
    class Meta:
        abstract = True

    num = models.BigAutoField(primary_key=True)

    title = models.CharField(max_length=64, null=True)
    username = models.CharField(max_length=64, null=True)

    type = models.CharField(max_length=128, null=False)

    date = models.BigIntegerField(null=True)
    # big_file_id
    photo = models.CharField(max_length=512, null=True)

    # big
    invite_link = models.CharField(max_length=256, null=True)
    members_count = models.BigIntegerField(null=True)
    available_reactions = models.TextField(max_length=1024, null=True)
    description = models.TextField(max_length=8196, null=True)

    hash = models.CharField(max_length=1024, null=False, unique=True)


class Chat(AbstractChat):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Chat'

    id = models.BigIntegerField(
        unique=True, verbose_name="Telegram Chat ID")


class ChatHistory(AbstractChat):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Chats History'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram Chat ID")


__all__ = ['Chat', 'ChatHistory', ]
