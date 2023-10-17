import os
import random
import binascii
import secrets
import hashlib

from io import BytesIO

import surge.bencoding as bencoding
from torrent_parser import TorrentFileParser, encode

from log import logger

from .default import DefaultTorrent, Metadata


class TorrentParse(DefaultTorrent):

    def gen_peer_id(self):
        if self.peer_id:
            return self.peer_id

        # peer_id = '-SP0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])
        # peer_id = '-qB0000-sMgqh9wQE.Z_'
        #     # seVcrets.token_bytes(20)
        # peer_id = '-PC0001-478269329936'
        peer_id = '-qB4450-spNmDQXWPXWj'
        self.peer_id = peer_id
        return peer_id

    def gen_info_hash(self):

        if not self.bytes_data:
            logger.info(f'no data')
            return

        try:
            self.bytes_data.seek(0)
            decoded_bytes = bencoding.decode(self.bytes_data.read())
            self.bytes_data.seek(0)
        except (TypeError, AttributeError):
            decoded_bytes = bencoding.decode(self.bytes_data)
            try:
                self.bytes_data.seek(0)
            except Exception:
                pass

        t = hashlib.sha1(
            bencoding.raw_val(bencoding.encode(decoded_bytes), b"info")
        ).digest()
        info_hash = binascii.hexlify(t).decode()
        logger.info(f'{info_hash=}')
        self.info_hash = info_hash
        return info_hash

    def gen_pieces_data(self):
        return {
            f'{p.index}_{binascii.hexlify(p.hash).decode()}': p for p in self.metadata.pieces
        }

    def parse(self):

        if self.parsed:
            return

        # self.metadata = Metadata(Metadata)

        try:
            self.bytes_data.seek(0)
            data = TorrentFileParser(self.bytes_data.read()).parse()
            self.bytes_data.seek(0)
            self.metadata = Metadata.from_bytes(self.bytes_data.read())
            # self.metadata.from_bytes(self.bytes_data.read())
            self.bytes_data.seek(0)
        except AttributeError:
            logger.info(f'2')
            self.metadata = Metadata.from_bytes(self.bytes_data)
            data = TorrentFileParser(self.bytes_data).parse()
            # self.metadata.from_bytes(self.bytes_data)

        self.count = len(self.metadata.pieces)

        logger.info(f'{len(self.metadata.pieces)=}')

        self.file_data = data

        self.gen_info_hash()
        self.name = data['info']['name']
        if isinstance(self.name, bytes):
            for encoding in ('utf8', 'cp1251'):
                try:
                    name = data['info']['name'].decode(encoding)
                    logger.info(f'{self.name} handled by {encoding=}')
                    self.name = name
                    break
                except Exception as exc:
                    logger.info(f'{self.name=}, {exc=}')
                    continue
            else:
                logger.info(f'no one encoding handled {self.name=}, {self.info_hash=}')

        try:
            announce_list = [
                data['announce'],
                *[item for sublist in data["announce-list"] for item in sublist]
            ]
        except KeyError:
            announce_list = []

        try:
            url_list = data["url-list"]
        except KeyError:
            url_list = []

        for tracker in (
                *self.extra_trackers, *announce_list.copy()
        ):
            if tracker not in self.metadata.announce_list:
                self.metadata.announce_list.append(tracker)

            if tracker not in announce_list:
                announce_list.append(tracker)

        # logger.info(f'{announce_list=}')

        announce_list = list(set(announce_list))
        # logger.info(f'{id(self.metadata)=}')
        self.metadata.announce_list = announce_list

        self.announce_list = '\n'.join(announce_list)
        self.url_list = '\n'.join(url_list)

        self.publisher = self.metadata.publisher
        self.publisher_url = self.metadata.publisher_url

        self.comment = self.metadata.comment
        self.creation_date = self.metadata.creation_date
        self.created_by = self.metadata.created_by

        # self.gen_pieces_hash()
        self.gen_peer_id()

        self.parsed = True


def test_torrent_parse():

    logger.info(f'')
    cls = []
    for n in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15):

        path = f'test{n}.torrent'

        if not os.path.isfile(path):
            continue

        logger.info(f'testing torrent: {n=}')
        with open(path, 'rb') as f:

            cl = TorrentParse(file=f)
            cl.parse()
            cls.append(cl)

            logger.info(f'{cl.metadata.comment=}')
            logger.info(f'{cl.metadata.pieces[0]=}')

    logger.info(f'---------------')
    for cl in cls:
        logger.info(f'{cl.metadata.comment=}')
        logger.info(f'{cl.metadata.pieces[0]=}')
