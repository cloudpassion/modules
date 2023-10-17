import redis
import dataclasses

from io import BytesIO
from collections import deque
from typing import Dict, Optional, List

from config import secrets
from log import logger

from ..piece.default import Metadata


class AbstractTorrent:

    name: str
    announce_list: str
    url_list: str
    created_by: str
    creation_date: int
    comment: str
    publisher: str
    publisher_url: str

    announce: str
    info: str

    count: int
    info_hash: str


class DefaultTorrent(AbstractTorrent):

    parsed: bool
    pieces: List
    data: deque
    peer_id: str
    extra_trackers = [
        'http://retracker.local/announce',
        'http://tor2merun.local/announce',
        'http://qbwin.local/announce',
        'http://qb.local/announce',
        'http://127.0.0.1:9000/announce',
    ]

    file_data: Dict
    bytes_data: BytesIO
    metadata: Metadata
    redis: redis.Redis

    def __init__(
            self, file=None, bytes_data=None,
            pieces=None
    ):

        try:
            getattr(self, 'bytes_data')
        except AttributeError:
            self.bytes_data = None

        if file:
            self.bytes_data = file.read()

        if bytes_data:
            self.bytes_data = bytes_data

        if pieces:
            self.pieces = pieces
        else:
            try:
                getattr(self, 'pieces')
            except AttributeError:
                self.pieces = []

        self.redis = redis.Redis(host='localhost', port=6379, db=12)

        for key in (
            'parsed', 'peer_id', 'name',
            'announce_list', 'url_list',
            'created_by', 'creation_date',
            'comment', 'publisher',
            'publisher_url', 'announce',
            'info', 'info_hash'
        ):
            try:
                getattr(self, key)
            except AttributeError:
                setattr(self, key, None)

        self.data = deque()

        try:
            extra_peers = secrets.bt.extra_peers
        except AttributeError:
            extra_peers = []

        self.extra_peers = extra_peers


def test_torrent_default():

    with open('test2.torrent', 'rb') as f:

        cl = DefaultTorrent(file=f)
        cl.metadata.from_bytes(cl.bytes_data)

        logger.info(f'{dir(cl.metadata)}')

        # logger.info(f'{cl.metadata.info}')
        logger.info(f'{cl.metadata.info_hash}')
        logger.info(f'{cl.metadata.announce_list}')
        logger.info(f'{cl.metadata.files}')

        logger.info(f'{cl.metadata.creation_date}')
        logger.info(f'{cl.metadata.created_by}')
        logger.info(f'{cl.metadata.publisher}')
        logger.info(f'{cl.metadata.publisher_url}')


