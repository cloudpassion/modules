from django.db import models
from django.db.models import F


class ExtraBasedModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    hash = models.CharField(
        default=False,
        max_length=1024, null=False, unique=True
    )
