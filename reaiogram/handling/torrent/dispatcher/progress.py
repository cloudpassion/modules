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
                status: TorrentStatus = self.torrents[info_hash]
            except KeyError:
                await asyncio.sleep(10)
                continue
            except Exception as exc:
                logger.info(f'{exc=} h0')
                break

            try:

                if not status.in_work:
                # if not torrent.missing_pieces:
                    logger.info(f'break status for {info_hash=}')
                    raise asyncio.CancelledError

                status.update_status(
                    torrent.pieces,
                    torrent.missing_pieces,
                    trackers.connected_trackers,
                    torrent.connected_peers,
                )

                await asyncio.sleep(random.randint(1, 5))

            except asyncio.CancelledError as exc:
                logger.info(f'{exc=} h1')

                status.update_status(
                    torrent.pieces,
                    0,
                    trackers.connected_trackers,
                    torrent.connected_peers,
                )
                break
            except Exception as exc:
                logger.info(f'{exc=} h2')
                await asyncio.sleep(120)

    async def _print_torrents_progress(
            self,
            to_file=False, to_console=False,
    ):
        update_interval = 10
        tmp_file = '/home/default/tmp/torrent.progress.txt'

        ms_total = 0

        while True:

            await asyncio.sleep(update_interval)
            status_lines = []

            # logger.info(f'{self.torrents=}')
            pre_diff = ms_total
            ms_total = 0

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
                        pass
                    if not status.total:
                        pass
                        # continue
                except AttributeError:
                    continue

                missing_diff = status.total - status.missing
                ms_total += status.missing

                line = f'{ERASE_LINE}' \
                       f'h: {torrent.info_hash} ' \
                       f'p: {missing_diff}/{status.total} ' \
                       f'tr: {status.connected_trackers}, ' \
                       f'pr: {status.connected_peers} ' \
                       f'n: {torrent.name[0:20]}'

                status_lines.append(line)

            status_lines.append(
                f'{ERASE_LINE}'
                f'\t: {pre_diff - ms_total} in {update_interval} secs'
            )

            # await asyncio.sleep(10)
            # continue

            if len(status_lines)-1 > 1:
                if to_file:
                    with open(tmp_file, 'w') as lw:
                        lw.write(
                            # f'\x1b[{1*len(status_lines)+1}A' +
                            # f'{ERASE_LINE}--------------------------------------\n'
                            # f'{ERASE_LINE}\n{ERASE_LINE}' +
                            f'\n'.join(status_lines) + '\r'
                        )
                if to_console:
                    print(
                        f'\x1b[{1*len(status_lines)+1}A' +
                        f'{ERASE_LINE}--------------------------------------\n'
                        f'{ERASE_LINE}\n{ERASE_LINE}' +
                        f'\n'.join(status_lines) + '\r',
                        end="",
                        flush=True,
                        )
            elif len(status_lines)-1 == 1:
                if to_file:
                    with open(tmp_file, 'w') as lw:
                        lw.write(
                            # f'\x1b[2A' +
                            # f'{ERASE_LINE}--------------------------------------\n'
                            # f'{ERASE_LINE}\n{ERASE_LINE}' +
                            f''.join(status_lines) + '\r'
                        )
                if to_console:
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
        asyncio.create_task(self._print_torrents_progress(to_file=True, to_console=False))
