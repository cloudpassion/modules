try:
    import ujson as json
except ImportError:
    import json

from base64 import b64decode

from config import secrets
from atiny.http import MyHttp
from log import logger

from .default import DefaultDHT


class DHTMakeTorrent(
    DefaultDHT
):

    async def get_from_http(
            self,
            info_hash=None,
            magnet=None,
    ):

        if not info_hash and not magnet:
            return

        if not magnet:
            magnet = f'magnet:?xt=urn:btih:{info_hash.lower()}'

        http = MyHttp()

        resp = await http.get(
            url=f'http://{secrets.bt.m2t.host}/?'
                f'apikey={secrets.bt.m2t.api}&'
                f'magnet={magnet}'

        )

        if resp.error or resp.status != 200:
            return

        js = json.loads(resp.content.decode('utf8'))
        status = js.get('status')
        logger.info(f'{status=}')

        if not status or status != 'success':
            return

        return b64decode(js.get('torrent_data'))


import pytest

@pytest.mark.asyncio
async def test_get_torrent():

    cl = DHTMakeTorrent()

    d = await cl.get_from_http(
        info_hash='753a81ea8c7e07d9e4040b8a0c1252a970e352ed'
    )

    logger.info(f'{d=}')

