from django.db import models


class ExtraBasedModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    db_hash = models.CharField(
        default=False,
        max_length=1024, null=False, unique=True,
        verbose_name='db_hash',
    )
