# from ..default import TimeBasedModel, models
#
#
# #
#
# class Poll(TimeBasedModel):
#
#     num = models.BigAutoField(primary_key=True)
#
#     id = models.BigIntegerField(unique=True, null=False)
#
#     question = models.TextField(max_length=4096)
#
#     total_voter_count = models.BigIntegerField()
#     is_closed = models.BooleanField()
#     is_anonymous = models.BooleanField()
#     allow_multiple_answers = models.BooleanField()
#
#     type = models.CharField(max_length=128)
#     options = models.TextField(max_length=8196)
#
#
# class Reaction(TimeBasedModel):
#
#     num = models.BigAutoField(primary_key=True)
#     reaction = models.CharField(unique=True, max_length=256)
#     title = models.CharField(max_length=128)
#
#     hash = models.CharField(max_length=1024, null=False, unique=True)
#
#
# __all__ = [
#     'Poll', 'Reaction',
# ]
