from io import BytesIO

from log import logger

from .default import PiecesInTxtDefault


class PiecesMetadataInTxtVersion6(
    PiecesInTxtDefault
):

    def read_text_data_version6(
            self, from_bytes: bytes,
    ):
        if isinstance(from_bytes, BytesIO):
            from_bytes = from_bytes.read()
        #     from_bytes.seek(0)
        # else:
        #     _from_bytes = from_bytes

        try:
            text = from_bytes.decode('utf8')
            hash_file_metadata = []
            for x in text.splitlines():

                # logger.info(f'{x=}')
                seek = int(x.split('|')[0])
                info_hash = x.split('|')[2]
                try:
                    length = int(x.split('|')[1])
                except ValueError:
                    length = ''

                hash_file_metadata.append(
                    [info_hash, seek, length]
                )

            return hash_file_metadata
        except Exception:
            return {}



# def test_read_bytes():
#
#     cl = PiecesMetadataInTxtVersion2()
#
#     with open('34af699d199c4b87d0602796acdf05a94975dabf_53926d57ced66bdfd34ebd9.txt', 'rb') as f:
#         cl.read_text_data_version2(from_bytes=f.read())
