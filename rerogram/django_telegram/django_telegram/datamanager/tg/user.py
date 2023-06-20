from ..default import TimeBasedModel, models


class AbstractUser(TimeBasedModel):
    class Meta:
        abstract = True

    num = models.BigAutoField(primary_key=True)

    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    username = models.CharField(max_length=128, null=True)
    phone_number = models.CharField(max_length=256, null=True)
    photo = models.CharField(max_length=512, null=True)

    hash = models.CharField(max_length=1024, null=False, unique=True)


class User(AbstractUser):
    class Meta:
        app_label = 'datamanager'
        verbose_name = "User"

    id = models.BigIntegerField(
        unique=True, verbose_name="Telegram User ID"
    )

    deleted = models.BooleanField(default=False, null=True)


class UserHistory(AbstractUser):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Users History'

    id = models.BigIntegerField(
        unique=False, verbose_name="Telegram User ID"
    )


class Contact(TimeBasedModel):
    class Meta:
        app_label = 'datamanager'

    num = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User, unique=False, null=False,
        on_delete=models.CASCADE
    )

    hint = models.CharField(max_length=1024, null=True)

    contact_name = models.CharField(max_length=1024)
    from_chat_names = models.CharField(max_length=1024, null=True)
    from_chat_ids = models.CharField(max_length=1024, null=True)

    notify_ignore = models.BooleanField(default=False)
    add_ignore = models.BooleanField(default=False)
    pm_ignore = models.BooleanField(default=False)

    hash = models.CharField(max_length=1024, null=False, unique=True)


__all__ = [
    'User', 'UserHistory', 'Contact',
]
