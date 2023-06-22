from reaiogram.django_telegram.django_telegram.datamanager.default import ExtraBasedModel, models


DEFAULT_FILE_KEYS = (
    'file_id',
    'file_unique_id',

    'file_name',
    'mime_type',
    'file_size',
    'thumbnail',

    'chat',

    'md5',
    'path',
    'name',
    'hint',
    'tag',


)

DEFAULT_FILE_SELECT_KEYS = ('file_id', )


class AbstractFile(ExtraBasedModel):
    class Meta:
        abstract = True

    num = models.BigAutoField(primary_key=True)

    # tg
    file_id = models.TextField(max_length=8192, null=False)
    file_unique_id = models.TextField(max_length=8192, null=False)

    # tg extra
    file_name = models.CharField(max_length=528, null=True, blank=True)
    mime_type = models.CharField(max_length=64, default=False, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    # thumbnail = models.BigIntegerField(null=True, blank=True)

    # tg help
    chat = models.ForeignKey(
        'TgChat',
        on_delete=models.DO_NOTHING,
        null=True, blank=True,
    )
    # contact = models.ForeignKey(
    #     'TgUser',
    #     on_delete=models.DO_NOTHING,
    #     null=True,
    # )
    #
    # media_group_id = models.BigIntegerField(default=None, null=True)
    # chat_id = models.BigIntegerField(
    #     unique=False, null=True
    # )

    # local
    md5 = models.CharField(max_length=128, null=True, blank=True)
    hash_type = models.CharField(
        max_length=32, default=None,
        null=True, blank=True
    )
    path = models.CharField(max_length=1024, null=True, blank=True)
    hint = models.TextField(max_length=3000, null=True, blank=True)
    tag = models.CharField(max_length=128, null=True, blank=True)


# class TgFile(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'File'
#
#     type = models.CharField(max_length=32, default='document', null=False)


# class TgVideo(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Video'
#
#     type = models.CharField(max_length=32, default='video')
#     mime = models.CharField(max_length=64, default=False, null=True)
#
#
# class TgVoice(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Voice'
#
#     type = models.CharField(max_length=32, default='voice')
#     mime = models.CharField(max_length=64, default=False, null=True)
#     duration = models.BigIntegerField(null=True)
#     waveform = models.TextField(max_length=8196, null=True)
#
#
# class TgAudio(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Audio'
#
#     type = models.CharField(max_length=32, default='audio')
#     mime = models.CharField(max_length=64, default=False, null=True)
#     duration = models.BigIntegerField(null=True)
#
#
# class TgPhoto(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Photo'
#
#     big_file_id = models.CharField(max_length=512, null=True)
#     big_photo_unique_id = models.CharField(max_length=256, null=True)
#     small_file_id = models.CharField(max_length=512, null=True)
#     small_photo_unique_id = models.CharField(max_length=256, null=True)
#
#     type = models.CharField(max_length=32, default='photo')
#
#
# class TgSticker(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Sticker'
#
#     is_animated = models.BooleanField()
#     emoji = models.CharField(max_length=256)
#     set_name = models.CharField(max_length=512)
#     mime = models.CharField(max_length=64, default=False, null=True)
#
#
# class TgThumb(AbstractFile):
#     class Meta:
#         app_label = 'datamanager'
#         verbose_name = 'Thumb'
#
#     width = models.IntegerField(null=True)
#     height = models.IntegerField(null=True)
#
#     main_md5 = models.CharField(max_length=1024, null=True)


# __all__ = (
#     'TgFile',
#     # 'TgPhoto', 'TgVideo', 'TgVoice', 'TgAudio',
#     # 'TgSticker', 'TgThumb',
# )
