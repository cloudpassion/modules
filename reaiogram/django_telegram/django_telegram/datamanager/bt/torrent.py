from ..default import models, ExtraBasedModel
from ..tg.message import TgMessage

TORRENT_KEYS = [
    'info_hash',
    'name',
    'message',
    'info',

    'comment',
    'created_by',
    'creation_date',

    'announce_list',
    'url_list',

    'publisher',
    'publisher-url',

    'count',
]
TORRENT_SELECT_KEYS = [
    'info_hash',
]
TORRENT_HASH_KEY = 'torrent'
TORRENT_HASH_KEYS = TORRENT_KEYS


class AbstractTorrentFile(ExtraBasedModel):

    class Meta:
        app_label = 'datamanager'
        abstract = True

    db_keys = TORRENT_KEYS
    select_keys = TORRENT_SELECT_KEYS
    hash_key = TORRENT_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    name = models.TextField(
        max_length=4096, null=False
    )

    message = models.ForeignKey(
        TgMessage,
        on_delete=models.DO_NOTHING,
        null=True, blank=True,
    )

    info = models.TextField(
        max_length=16384, null=True, blank=True
    )

    comment = models.CharField(max_length=32768, null=True, blank=True)
    created_by = models.CharField(max_length=1024, null=True, blank=True)
    creation_date = models.BigIntegerField(null=True, blank=True)
    #
    announce_list = models.TextField(max_length=163840, null=True, blank=True)
    url_list = models.TextField(max_length=163840, null=True, blank=True)
    #
    publisher = models.CharField(max_length=1024, null=True, blank=True)
    publisher_url = models.CharField(max_length=1024, null=True, blank=True)

    redown_skip = models.BooleanField(null=True, blank=True)

    count = models.BigIntegerField(null=True, blank=True)


class TorrentFile(AbstractTorrentFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TorrentFile'

    info_hash = models.CharField(
        max_length=2048,
        unique=True,
        null=False
    )


class TorrentFileHistory(AbstractTorrentFile):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TorrentFiles History'

    info_hash = models.CharField(
        max_length=2048,
        unique=False,
        null=False
    )


__all__ = ['TorrentFile', 'TorrentFileHistory', ]
