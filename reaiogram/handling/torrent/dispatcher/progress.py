import asyncio
import random

from log import logger

from bt.torrent.file.download.surge import Torrent
from bt.tracker.resurge import Trackers

from ....dispatcher.default import ExtraDispatcher
from ....types.torrent.torrent import TorrentFile
from ....types.torrent.status import TorrentStatus


CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'
T_LINE = "\r\x1b[K"


class TorrentProgressDispatcher(
    ExtraDispatcher,
):

    torrents: dict = {}

    async def _pick_surge_progress(
            self,
            torrent: Torrent,
            trackers: Trackers,
            info_hash: str,
    ):

        while True:
            try:
                try:
                    status: TorrentStatus = self.torrents[info_hash]
                except KeyError:
                    await asyncio.sleep(10)
                    continue

                if not torrent.missing_pieces:
                    logger.info(f'break status for {info_hash=}')
                    break

                status.update_status(
                    torrent.pieces,
                    torrent.missing_pieces,
                    trackers.connected_trackers,
                    torrent.connected_peers,
                )

                await asyncio.sleep(random.randint(1, 5))

            except asyncio.CancelledError as exc:
                logger.info(f'{exc=} h1')
                # break
                raise

    async def _print_torrents_progress(self):
        update_interval = 10

        while True:

            await asyncio.sleep(update_interval)
            status_lines = []

            # logger.info(f'{self.torrents=}')
            for info_hash, status in self.torrents.items():
                # logger.info(f'{info_hash=}, {status=}')
                status: TorrentStatus

                if not status or not status.in_work or not status.torrent:
                    continue

                torrent: TorrentFile = status.torrent
                if not torrent:
                    continue

                try:
                    if not status.missing:
                        continue
                except AttributeError:
                    continue

                line = f'{ERASE_LINE}' \
                       f'h: {torrent.info_hash} ' \
                       f'p: {status.total - status.missing}/{status.total} ' \
                       f'tr: {status.connected_trackers}, ' \
                       f'pr: {status.connected_peers} ' \
                       f'n: {torrent.name[0:20]}'

                status_lines.append(line)

            # await asyncio.sleep(10)
            # continue

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
                    f'\x1b[2A' +
                    f'{ERASE_LINE}--------------------------------------\n'
                    f'{ERASE_LINE}\n{ERASE_LINE}' +
                    f''.join(status_lines) + '\r',
                    end="",
                    flush=True,
                    )
            else:
                await asyncio.sleep(10)

    async def _aextra_torrent_status_print(self):
        asyncio.create_task(self._print_torrents_progress())
