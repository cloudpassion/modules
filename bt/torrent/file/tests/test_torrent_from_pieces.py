from ..rw import TorrentReadWrite


def test_read_bytes():

    cl = TorrentReadWrite()
    with open('test10.torrent', 'rb') as f:
        cl.metadata.from_bytes(f.read())

    cl.merge_pieces(
        out_dir='.out',
        merge_from='files',
        metadata_from='txt',
        txt_dir='.txt_tmp',
        pieces_dir='.data_tmp',
        version=2,
    )

