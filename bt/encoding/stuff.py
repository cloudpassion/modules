import binascii
import urllib.parse

from log import logger


def from_query(info_hash):
    _info_hash = urllib.parse.unquote_to_bytes(info_hash)
    _info_hash = binascii.b2a_hex(_info_hash).decode('utf8')
    return _info_hash


def from_hex_to_bytes(info_hash: str):
    _bytes = binascii.unhexlify(info_hash)
    return _bytes


def from_bytes_to_hex(_bytes: bytes):
    # _bytes = binascii.hexlify(info_hash)
    info_hash = binascii.hexlify(_bytes).decode()
    return info_hash


def to_query(info_hash: str):

    logger.info(f'{info_hash=}')
    _info_hash = from_hex_to_bytes(info_hash)
    logger.info(f'{_info_hash}')
    _info_hash = urllib.parse.quote_from_bytes(_info_hash)
    return _info_hash


def test_bytes():
    # with open('.'):
    p = from_bytes_to_hex(b'Q^\xac\x87*2/\xf3\xc1\xb4[\x190\x11\xa0\xc6`\xc4\xbce')

    logger.info(f'{p=}')
    # assert p ==
