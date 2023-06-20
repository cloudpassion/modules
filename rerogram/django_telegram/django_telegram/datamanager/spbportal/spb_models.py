from ..default import TimeBasedModel, models
from ..tg.message import Message


class SpbPortalProblem(TimeBasedModel):

    num = models.BigAutoField(primary_key=True)

    # problem_num = models.BigIntegerField(unique=True)
    id = models.CharField(max_length=512, unique=True)

    message = models.ForeignKey(
        Message, unique=True, null=False,
        on_delete=models.DO_NOTHING,
    )

    text = models.TextField(max_length=8196, null=True)

    link = models.CharField(max_length=4096, null=False)
    type = models.CharField(max_length=1024, null=False)

    status = models.CharField(max_length=1024, null=False)
    title = models.CharField(max_length=1024, null=False)
    date = models.BigIntegerField(null=False)

    category = models.CharField(max_length=1024, null=True)
    reason = models.CharField(max_length=1024, null=True)
    solved_under = models.BigIntegerField(null=True)

    author_name = models.CharField(max_length=1024, null=True)
    author_id = models.BigIntegerField(null=True)
    join = models.BigIntegerField(null=True)

    hash = models.CharField(max_length=1024, null=False, unique=True)


class SpbPortalPagePost(TimeBasedModel):

    num = models.BigAutoField(primary_key=True)

    id = models.CharField(max_length=512, null=False)

    problem = models.ForeignKey(
        SpbPortalProblem, unique=False, null=False,
        on_delete=models.CASCADE
    )

    message = models.ForeignKey(
        Message, unique=True, null=False,
        on_delete=models.DO_NOTHING,
    )

    post_num = models.BigIntegerField()

    title = models.CharField(max_length=1024, null=False)
    author = models.CharField(max_length=1024, null=True)
    date = models.BigIntegerField(null=False)
    text = models.TextField(max_length=8196, null=True)
    status = models.TextField(max_length=1024, null=True)

    chat_message_ids = models.TextField(max_length=1024, null=True)

    post_files = models.TextField(max_length=8196, null=True)

    hash = models.CharField(max_length=1024, null=False, unique=True)


__all__ = [
    'SpbPortalProblem', 'SpbPortalPagePost'
]
