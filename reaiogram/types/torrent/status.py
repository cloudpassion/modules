
class TorrentStatus:

    in_work: bool

    total: int
    missing: int
    connected_trackers: int
    connected_peers: int

    def __init__(self):
        self.in_work = False
        self.torrent = None

    def to_work(self):
        self.in_work = True

    def from_work(self):
        self.in_work = False

    def is_work(self):
        return self.in_work

    def set_torrent(self, torrent):
        self.torrent = torrent

    def update_status(
            self, total, missing, connected_trackers, connected_peers
    ):
        self.total = total
        self.missing = missing
        self.connected_trackers = connected_trackers
        self.connected_peers = connected_peers
