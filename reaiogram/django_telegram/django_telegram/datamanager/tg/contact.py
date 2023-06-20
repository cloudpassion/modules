# from ..default import TimeBasedModel, models
# from .user import TgUser
#
#
# class TgContact(TimeBasedModel):
#     class Meta:
#         app_label = 'datamanager'
#
#     num = models.BigAutoField(primary_key=True)
#
#     user = models.ForeignKey(
#         TgUser, unique=False, null=False,
#         on_delete=models.CASCADE
#     )
#
#     hint = models.CharField(max_length=1024, null=True)
#
#     contact_name = models.CharField(max_length=1024)
#     from_chat_names = models.CharField(max_length=1024, null=True)
#     from_chat_ids = models.CharField(max_length=1024, null=True)
#
#     notify_ignore = models.BooleanField(default=False)
#     add_ignore = models.BooleanField(default=False)
#     pm_ignore = models.BooleanField(default=False)
#
#     hash = models.CharField(max_length=1024, null=False, unique=True)
#
#
# __all__ = [
#     'TgContact',
# ]
