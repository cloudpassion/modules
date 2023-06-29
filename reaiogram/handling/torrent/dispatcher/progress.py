import asyncio

from bt.torrent.file.download.surge import Torrent
from bt.tracker.resurge import Trackers

from ....dispatcher.default import ExtraDispatcher


class TorrentProgressDispatcher(
    ExtraDispatcher,
):

    torrents: dict = {
        'temp_info_hash': {

        }
    }

    def _pick_surge_progress(
            self, torrent: Torrent, trackers: Trackers, info_hash: str,
    ):
        total = torrent.pieces
        missing = torrent.missing_pieces

        connected_trackers = trackers.connected_trackers
        connected_peers = torrent.connected_peers

    async def _print_torrents_progress(self):
        update_interval = 2

        while True:

            await asyncio.sleep(update_interval)

            print('progress')