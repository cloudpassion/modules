import surge.bencoding as bencoding

from log import logger


def decode(bs):
    """Return the Python object corresponding to `bs`.

    Raise `ValueError` if `bs` is not valid BEncoding.
    """
    start, rval = decode_from(bs, 0)
    if start == len(bs):
        return rval
    raise ValueError(f"Leftover bytes at index {start}.")


def decode_from(bs, start):
    try:
        token = bs[start]
    except IndexError as exc:
        raise ValueError(f"Expected more input at index {start}.") from exc
    if token == ord("i"):
        return bencoding._decode_int(bs, start)
    if token == ord("l"):
        return bencoding._decode_list(bs, start)
    if token == ord("d"):
        return bencoding._decode_dict(bs, start)
    if ord("0") <= token <= ord("9"):
        return bencoding._decode_bytes(bs, start)

    # logger.info(f'{bs=}, {start=}')
    raise ValueError(f"Unexpected token at index {start}.")
