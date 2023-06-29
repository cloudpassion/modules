from ..default import models, ExtraBasedModel
from ..tg.message import TgMessage

from .torrent import TorrentFile

PIECE_KEYS = [

    'info_hash',

    'torrent',
    'message',

    'version',
    'length',
    'begin',

    'resume_data',
]

PIECE_SELECT_KEYS = [
    'torrent', 'info_hash',
]

PIECE_HASH_KEY = 'piece'
PIECE_HASH_KEYS = [
    'info_hash',
    'torrent.info_hash',
]


class TorrentPiece(ExtraBasedModel):
    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TorrentPiece'

    db_keys = PIECE_KEYS
    select_keys = PIECE_SELECT_KEYS
    hash_key = PIECE_HASH_KEY

    num = models.BigAutoField(primary_key=True)

    info_hash = models.CharField(max_length=2048, null=False)

    torrent = models.ForeignKey(
        TorrentFile,
        on_delete=models.DO_NOTHING,
        null=False,
    )

    message = models.ForeignKey(
        TgMessage,
        on_delete=models.DO_NOTHING,
        null=True, blank=True,
    )

    version = models.BigIntegerField(
        null=True, blank=True,
        verbose_name='Upload version'
    )
    length = models.BigIntegerField()
    begin = models.BigIntegerField(null=True, blank=True)

    resume_data = models.TextField(max_length=67108864, null=True, blank=True)


__all__ = ('TorrentPiece', )
