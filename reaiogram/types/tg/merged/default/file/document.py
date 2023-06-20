from ..default import AbstractMergedTelegram

from reaiogram.django_telegram.django_telegram.datamanager.tg.file.document import (
    DOCUMENT_KEYS, DOCUMENT_SELECT_KEYS, DOCUMENT_HASH_KEY,
)


class AbstractMergedDocument(
    AbstractMergedTelegram
):

    hash_key = DOCUMENT_HASH_KEY
    db_keys = DOCUMENT_KEYS
    select_keys = DOCUMENT_SELECT_KEYS

    file_unique_id: str
