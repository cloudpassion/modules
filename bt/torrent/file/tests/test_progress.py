import asyncio
import random
import pytest


async def _pick_surge_progress(
        status,
        pieces,
        missing_pieces,
        connected_trackers,
        connected_peers,
        info_hash: str,
):

    while True:
        try:

            status.update({
                'pieces': pieces,
                'missing_pieces': missing_pieces,
                'connected_trackers': connected_trackers,
                'connected_peers': connected_peers,
            })

            await asyncio.sleep(random.randint(1, 5))

        except asyncio.CancelledError:
            raise


@pytest.mark.asyncio
async def test_progress():

    pieces = 1000
    missing_pieces = 100
    connected_trackers = 19
    connected_peers = 10

    s1 = {}
    s2 = {}
    s3 = {}

    asyncio.create_task(_pick_surge_progress(
        s1, pieces, missing_pieces, connected_trackers, connected_peers, 'asdfasdfasdf'
    ))

    asyncio.create_task(_pick_surge_progress(
        s2, pieces, missing_pieces, connected_trackers, connected_peers, '23412341234'
    ))

    asyncio.create_task(_pick_surge_progress(
        s3, pieces, missing_pieces, connected_trackers, connected_peers, 'xxxxxxxx'
    ))

    statuses = {
        'asdfasdfasdf': s1,
        # '23412341234': s2,
        # 'xxxxxxxx': s3,
    }

    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    T_LINE = "\r\x1b[K"

    while True:

        await asyncio.sleep(2)
        status_lines = []

        # logger.info(f'{self.torrents=}')
        for info_hash, status in statuses.items():
            try:
                total = status.get('pieces')
                missing = status.get('missing_pieces')
                tr = status.get('connected_trackers')
                pr = status.get('connected_peers')

                line = f'{ERASE_LINE}' \
                       f'h: {info_hash} ' \
                       f'p: {total - missing}/{total} ' \
                       f'tr: {tr}, ' \
                       f'pr: {pr}'

                status_lines.append(line)
            except AttributeError:
                continue

        if len(status_lines) > 1:
            print(
                f'\x1b[{1*len(status_lines)+1}A' +
                f'{ERASE_LINE}--------------------------------------\n'
                f'{ERASE_LINE}\n{ERASE_LINE}' +
                f'\n'.join(status_lines) + '\r',
                end="",
                flush=True,
            )
        elif len(status_lines) == 1:
            print(
                f'\x1b[{2}A' +
                f'{ERASE_LINE}--------------------------------------\n'
                f'{ERASE_LINE}\n{ERASE_LINE}' +
                f''.join(status_lines) + '\r',
                end="",
                flush=True,
                )
        else:
            await asyncio.sleep(1)


asyncio.run(test_progress())
