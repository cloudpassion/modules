from ..default import TimeBasedModel, models
from typing import Union


class AbstractFile(TimeBasedModel):
    class Meta:
        abstract = True

    num = models.BigAutoField(primary_key=True)

    file_id = models.CharField(max_length=512, null=False)

    md5 = models.CharField(max_length=128, unique=True, null=False)
    hash_type = models.CharField(max_length=32, default='md5')
    file_unique_id = models.CharField(max_length=256, null=False)
    size = models.IntegerField(null=True)
    path = models.CharField(max_length=256, null=True)

    name = models.CharField(max_length=528, unique=False, null=True)
    hint = models.TextField(max_length=3000, null=True)

    chat_id = models.BigIntegerField(
        unique=False, null=True
    )
    extension = models.CharField(max_length=16, null=True)

    tag = models.CharField(max_length=128, null=True)

    date = models.BigIntegerField(null=True)
    media_group_id = models.BigIntegerField(default=None, null=True)


class TgFile(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'File'

    type = models.CharField(max_length=32, default='document')
    mime = models.CharField(max_length=64, default=False, null=True)


class TgVideo(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Video'

    type = models.CharField(max_length=32, default='video')
    mime = models.CharField(max_length=64, default=False, null=True)


class TgVoice(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Voice'

    type = models.CharField(max_length=32, default='voice')
    mime = models.CharField(max_length=64, default=False, null=True)
    duration = models.BigIntegerField(null=True)
    waveform = models.TextField(max_length=8196, null=True)


class TgAudio(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Audio'

    type = models.CharField(max_length=32, default='audio')
    mime = models.CharField(max_length=64, default=False, null=True)
    duration = models.BigIntegerField(null=True)


class TgPhoto(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Photo'

    big_file_id = models.CharField(max_length=512, null=True)
    big_photo_unique_id = models.CharField(max_length=256, null=True)
    small_file_id = models.CharField(max_length=512, null=True)
    small_photo_unique_id = models.CharField(max_length=256, null=True)

    type = models.CharField(max_length=32, default='photo')


class TgSticker(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Sticker'

    is_animated = models.BooleanField()
    emoji = models.CharField(max_length=256)
    set_name = models.CharField(max_length=512)
    mime = models.CharField(max_length=64, default=False, null=True)


class TgThumb(AbstractFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'Thumb'

    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)

    main_md5 = models.CharField(max_length=1024, null=True)


__all__ = (
    'TgFile', 'TgPhoto', 'TgVideo', 'TgVoice', 'TgAudio',
    'TgSticker', 'TgThumb',
)
