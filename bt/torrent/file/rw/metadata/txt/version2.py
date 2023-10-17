from io import BytesIO

from log import logger

from .default import PiecesInTxtDefault


class PiecesMetadataInTxtVersion2(
    PiecesInTxtDefault
):

    def read_text_data_version2(
            self, from_bytes: bytes,
    ):

        if isinstance(from_bytes, BytesIO):
            from_bytes = from_bytes.read()
        #     from_bytes.seek(0)
        # else:
        #     _from_bytes = from_bytes

        try:
            text = from_bytes.decode('utf8')
            hash_file_metadata = {
                x.split('|')[1]:
                    int(x.split('|')[0]) for x in text.splitlines()
            }

            return hash_file_metadata
        except Exception:
            return {}
