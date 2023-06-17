from ..default import TimeBasedModel, models, ParseModel


class Bot(TimeBasedModel):

    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Bot'

    id = models.BigAutoField(primary_key=True)

    bot_id = models.BigIntegerField(
        unique=True, verbose_name="Telegram Bot ID"
    )
    is_bot = models.BooleanField(default=True)

    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    username = models.CharField(max_length=64, null=True)

    language_code = models.CharField(max_length=32, null=True)

    can_join_groups = models.BooleanField()
    can_read_all_group_messages = models.BooleanField()
    supports_inline_queries = models.BooleanField()

    # flag if bot configs updated
    updated = models.BooleanField(default=False)


class BotConfig(ParseModel):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Bot Config'
        verbose_name_plural = 'Bots Config'

    id = models.ForeignKey(Bot, unique=True, primary_key=True, on_delete=models.CASCADE)

    # <bot, this for allow configure bot from private message in telegram
    creator = models.BigIntegerField(
        unique=True, verbose_name="Telegram Creator ID", null=True
    )

    have_superadmin = models.BooleanField(default=False)
    super_admin_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    have_admin = models.BooleanField(default=False)
    admin_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    # /bot>
    # <stuff, workers
    have_moderator = models.BooleanField(default=False)
    moderators_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    have_writer = models.BooleanField(default=False)
    writers_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    have_stuff = models.BooleanField(default=False)
    stuff_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    # /stuff>

    # <people, other people allow or not used this bot
    have_block = models.BooleanField(default=False)
    blocked_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    have_allow = models.BooleanField(default=False)
    allowed_prefix = models.CharField(
        max_length=15, unique=True, null=False
    )
    have_walker = models.BooleanField(default=True)
    # /people>

    # <parse, this for parse or not group of updates received from users above
    # some from ParseModel
    parse_channel = models.BooleanField(default=False)
    parse_poll = models.BooleanField(default=False)
    parse_system = models.BooleanField(default=False)
    parse_other = models.BooleanField(default=False)
    # /parse>


class Role(ParseModel):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Role'

    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=16, null=True, unique=True)
    description = models.TextField(max_length=1024, null=True)

    # flags. allow or not parse from this groups
    # from ParseModel


__all__ = ('Bot', 'BotConfig', 'Role', )
