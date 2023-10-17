import binascii
import hashlib
import os

from log import logger

from .version2 import PiecesMetadataInTxtVersion2
from .version6 import PiecesMetadataInTxtVersion6


class PiecesMetadataInTxt(
    PiecesMetadataInTxtVersion2,
    PiecesMetadataInTxtVersion6,
):

    def __init__(self, version=2):
        self.version = version

    def txt_read_from_files(
            self, files=None, dir_path=None,
    ):
        if not files and not dir_path:
            return {}

        metadata = {}
        if dir_path and os.path.isdir(dir_path):
            files = [f'{dir_path}/{f}' for f in os.listdir(dir_path)]

        logger.info(f'{files=}')
        if files:
            for file_path in files:
                if not os.path.isfile(file_path):
                    logger.info(f'no file: {file_path=}')
                    continue

                with open(file_path, 'rb') as f:
                    metadata.update({
                        file_path: self._txt_read_from_bytes(
                            from_bytes=f.read()
                        )
                    })

        return metadata

    def txt_read_from_bytes(
            self, txt_bytes,
    ):
        metadata = {}
        # logger.info(f'{txt_bytes=}')
        for file_path, txt_b in txt_bytes:
            # rnd = binascii.hexlify(hashlib.sha1(txt_bytes).digest()).decode()
            metadata.update({
                # f'___{rnd}': self._txt_read_from_bytes(
                file_path: self._txt_read_from_bytes(
                    from_bytes=txt_b
                )
            })

        return metadata

    def _txt_read_from_bytes(self, from_bytes: bytes):
        if 2 <= self.version <= 5:
            return self.read_text_data_version2(from_bytes=from_bytes)

        if self.version == 6:
            return self.read_text_data_version6(from_bytes=from_bytes)


def test_read_bytes():

    cl = PiecesMetadataInTxt()
    meta = cl.txt_read_from_files(dir_path='.txt_tmp')

    logger.info(f'{meta=}')
