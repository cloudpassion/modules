import os
import functools

from io import BytesIO
from surge.protocol import build_file_tree
from surge.metadata import make_chunks, valid_piece_data

from log import logger, log_stack

from ..default import DefaultTorrent
from .metadata import PiecesMetadata
from ....encoding.stuff import from_hex_to_bytes


def seek_read(file_object, seek, length):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        file_object.seek(seek)
        data = file_object.read(length)
        yield data


class MergeTorrent(DefaultTorrent):

    def merge_pieces(
            self,
            out_dir,
            merge_from=None,
            metadata_from=None,
            version=None,
            txt_dir=None,
            pieces_dir=None,
            txt_metadata=None,
            txt_bytes=None,
            file_bytes=None,
            rebuild_tree=True,
    ):
        if rebuild_tree:
            logger.info(f'{rebuild_tree=}, {out_dir=}')

        # txt_bytes = [[file_name1, bytes_from_this_file], ...]
        # file_bytes = {file_name1: data_file_bytes], ...}

        if not txt_metadata:
            if metadata_from == 'txt':
                if not txt_dir or not version:
                    logger.info(f'need set txt_dir if merge_from=txt')
                    return

                cl = PiecesMetadata(version)
                txt_metadata = cl.txt_read_from_files(dir_path=txt_dir)

            if metadata_from == 'bytes':
                if not txt_bytes or not version:
                    logger.info(f'need set list of metadata bytes if metadata from bytes')
                    return

                cl = PiecesMetadata(version)
                txt_metadata = cl.txt_read_from_bytes(
                    txt_bytes=txt_bytes
                )

        if merge_from == 'files':
            if not pieces_dir:
                logger.info(f'need set pieces_dir if merge_from=files')
                return

        if merge_from == 'bytes':
            if not file_bytes:
                logger.info(f'need set file_bytes if merge_from=bytes')
                return

        if not txt_metadata:
            logger.info(f'didn know where txt_metadata stored')
            return

        # logger.info(f'{txt_metadata=}')
        if version == 6:
            return self._merge_pieces_version6(
                txt_metadata,
                merge_from,
                pieces_dir,
                file_bytes,
                rebuild_tree,
                out_dir
            )

        piece_length = max([
            x[1] for x in [
                list(d.values()) for d in [txt_metadata[x] for x in txt_metadata]
            ]
        ])
        logger.info(f'{piece_length=}')

        for file_path, file_data in txt_metadata.items():

            if merge_from == 'files':
                data_file_path = pieces_dir + '/' + file_path.split('/')[-1].replace('.txt', '.data')
                if not os.path.isfile(data_file_path):
                    logger.info(f'no file {data_file_path}')
                    continue

                data_f = open(data_file_path, 'rb')

            elif merge_from == 'bytes':
                data_f = file_bytes[file_path]
            else:
                logger.info(f'need to set merge_from')
                return

            results = []
            for info_hash, seek in file_data.items():

                # pieces_bytes[info_hash] = seek_read(data_f, seek, piece_length)
                data_f.seek(seek)
                if info_hash == 'c059bc0e7e9033b77fcf6f9807d3c83829a944aa':
                    logger.info(f'my bad. read other length....')
                    data = data_f.read(2216010)
                else:
                    data = data_f.read(piece_length)

                piece = [
                    p for p in self.metadata.pieces if (
                            p.hash == from_hex_to_bytes(info_hash)
                    )
                ][0]
                results.append([piece, data])

            self.write_pieces_to_tree(
                out_dir=out_dir,
                results=results,
                rebuild_tree=rebuild_tree,
            )

    def _merge_pieces_version6(
            self,
            txt_metadata,
            merge_from,
            pieces_dir,
            file_bytes,
            rebuild_tree,
            out_dir
    ):
        # logger.info(f'{txt_metadata=}')
        try:
            _t = [txt_metadata[x] for x in txt_metadata]
            # logger.info(f'{_t=}')
            t = [x[0] for x in _t if x]
            # logger.info(f'{t=}')
            piece_length = max([
                d[2] for d in t
            ])

        except Exception as exc:
            logger.info(f'def piece exc: {exc=}, {txt_metadata=}')
            with open(f'{self.info_hash}.txt.debug', 'a+') as fw:
                fw.write(f'{txt_metadata}')

        # logger.info(f'{piece_length=}')
        # quit()

        for file_path, file_data in txt_metadata.items():
            # logger.info(f'{file_path=}, {file_data=}')

            if merge_from == 'files':
                data_file_path = pieces_dir + '/' + file_path.split('/')[-1].replace('.txt', '.data')
                if not os.path.isfile(data_file_path):
                    logger.info(f'no file {data_file_path}')
                    continue

                data_f = open(data_file_path, 'rb')

            elif merge_from == 'bytes':
                data_f = file_bytes[file_path]
            else:
                logger.info(f'need to set merge_from')
                return

            results = []
            for info_hash, seek, length in file_data:

                if not length:
                    length = piece_length
                # else:
                #     logger.info(f'{length=}')

                # logger.info(f'{length=}')
                # pieces_bytes[info_hash] = seek_read(data_f, seek, piece_length)
                # logger.info(f'{info_hash=}, {seek=}, {length=}')
                data_f.seek(seek)
                data = data_f.read(length)

                piece = [
                    p for p in self.metadata.pieces if (
                            p.hash == from_hex_to_bytes(info_hash)
                    )
                ][0]
                ch = valid_piece_data(piece, data)
                if not ch:
                    logger.info(f'{ch=}, {info_hash=}, {seek=}, {length=}')

                results.append([piece, data])

            self.write_pieces_to_tree(
                out_dir=out_dir,
                results=results,
                rebuild_tree=rebuild_tree,
            )

    def write_pieces_to_tree(self, out_dir, results, rebuild_tree=True):
        # functools.partial(
        if rebuild_tree:
            build_file_tree(out_dir, self.metadata.files)

        chunks = make_chunks(self.metadata.pieces, self.metadata.files)
        for piece, data in results:
            for chunk in chunks[piece]:
                # functools.partial(
                chunk.write(out_dir, data)


def yield_available_pieces(
        pieces, folder, files, check_only=None
):
    chunks = make_chunks(pieces, files)
    for piece in pieces:
        if check_only and piece not in check_only:
            yield piece
            continue

        logger.info(f'check: {piece=}')
        data = []
        for chunk in chunks[piece]:
            try:
                data.append(chunk.read(folder))
            except FileNotFoundError:
                continue
        if valid_piece_data(piece, b"".join(data)):
            logger.info(f'ok: {piece=}')
            yield piece



def test_read_bytes():

    cl = MergeTorrent()

    cl.merge_pieces(
        out_dir='.out',
        merge_from='files',
        metadata_from='txt',
        txt_dir='.txt_tmp',
        pieces_dir='.data_tmp',
        version=2,

    )
