import os
import pytest
import urllib.parse

from log import logger


from ....tracker.resurge import Trackers, request_peers
from ... import TorrentFile
from ....encoding.stuff import from_query, to_query


@pytest.mark.asyncio
async def test_tracker():

    for n in (10, ):
        file_path = f'test{n}.torrent'
        if not os.path.isfile(file_path):
            continue

    with open(file_path, 'rb') as f:

        cl = TorrentFile(file=f)
        cl.parse()

        # t = to_query(cl.info_hash)
        # logger.info(f'{t=}')
        tr = Trackers(
            info_hash=cl.metadata.info_hash,
            peer_id=cl.peer_id,
            announce_list=[
                'http://bt.t-ru.org/ann?pk=ea6ca2d960e13cac69ee3c2dee079864',
                'http://tr1.tor4me.info/ann?uk=Ab19d5sSep',
                'http://retracker.local/announce',
                'http://retracker.local/announce',
                'http://tor2merun.local/announce',
                'http://qbwin.local/announce',
                'http://qb.local/announce',
            ],
            max_peers=50,
        )

        async with Trackers(
            cl.metadata.info_hash, cl.peer_id, tr._announce_list, 50,
        ) as trackers:
            peer = await trackers.get_peer()
            logger.info(f'{peer=}')

