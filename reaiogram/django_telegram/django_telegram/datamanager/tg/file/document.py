from .default import (
    AbstractFile, models,
    DEFAULT_FILE_KEYS, DEFAULT_FILE_SELECT_KEYS
)

DOCUMENT_KEYS = (
    *DEFAULT_FILE_KEYS,
)

DOCUMENT_SELECT_KEYS = (
    *DEFAULT_FILE_SELECT_KEYS,
)

DOCUMENT_HASH_KEY = 'document'


class TgDocument(AbstractFile):

    class Meta:
        app_label = 'datamanager'
        verbose_name = 'TgDocument'

    db_keys = DOCUMENT_KEYS
    select_keys = DOCUMENT_SELECT_KEYS
    hash_key = DOCUMENT_HASH_KEY


__all__ = [
    'TgDocument',
]
