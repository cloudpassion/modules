from surge.metadata import (
    yield_available_pieces,
)


class TorrentCheck:

    def yield_available_pieces(self, folder):
        return yield_available_pieces(self.metadata.pieces, folder, self.metadata.files)
