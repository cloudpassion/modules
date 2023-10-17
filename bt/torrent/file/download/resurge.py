import os
import aiofiles
import asyncio
import collections
import dataclasses
import random

from surge.metadata import (
    Chunk as DefaultChunk,
    File,
    Piece
)
from surge.protocol import (
    open_stream, messages, State,
    Queue as SurgeQueue,
    Block,
    Torrent as SurgeTorrent,
    valid_piece_data,
)
from surge.tracker import Peer as SurgePeer
from ....encoding.stuff import from_bytes_to_hex

from log import logger, log_stack


class Queue(SurgeQueue):
    #
    # def add_piece(self, piece):
    #     """Add `piece` to the download queue."""
    #     blocks = set(yield_blocks(piece))
    #     self._progress[piece] = Progress(piece, blocks)
    #     self._queue.extendleft(blocks)

    def put_block(self, block, data):
        """Deliver a downloaded block.

        Return the piece and its data if this block completes its piece.
        """
        if block not in self._requested:
            return None
        self._requested.remove(block)
        piece = block.piece
        progress = self._progress[piece]
        progress.add(block, data)
        if not progress.done:
            return None
        data = self._progress.pop(piece).data
        if valid_piece_data(piece, data):
            return piece, data

        logger.info(f'{piece.index=}')

        raise ValueError("Invalid data.")


@dataclasses.dataclass(frozen=True)
class Peer(SurgePeer):
    address: str
    port: int

    @classmethod
    def from_string(cls, s):
        return cls(s.split(':')[0], int(s.split(':')[1]))


class Torrent(
    SurgeTorrent,
):
    # def __init__(self, pieces, missing_pieces, results):
    #     self._missing_pieces = list(missing_pieces)
    #     self._peer_to_pieces = {}
    #     self._piece_to_peers = collections.defaultdict(set)
    #     self._pieces = pieces
    #     self._results = results
    #     # This check is necessary because `put_piece` is never called if there
    #     # are no pieces to download.
    #     if not self._missing_pieces:
    #         self._results.close_nowait()

    @property
    def connected_peers(self):
        """The number of connected peers."""
        return len(self._peer_to_pieces)

    def peer_connected(self, peer):
        self._peer_to_pieces[peer] = set()

    def peer_disconnected(self, peer):
        try:
            for piece in self._peer_to_pieces.pop(peer):
                self._piece_to_peers[piece].remove(peer)
                if not self._piece_to_peers[piece]:
                    self._piece_to_peers.pop(piece)
        except KeyError:
            pass
        except Exception as exc:
            logger.info(f'{exc=}')
            pass

    async def put_piece(self, peer, piece, data):
        """Deliver a downloaded piece."""
        if piece not in self._missing_pieces:
            return

        try:
            self._missing_pieces.remove(piece)
        except Exception as exc:
            logger.info(f'{exc=}'[:512])

        try:
            if peer:
                self._peer_to_pieces[peer].remove(piece)
                self._piece_to_peers[piece].remove(peer)
        except Exception as exc:
            logger.info(f'{exc=}'[:512])

        try:
            if self._piece_to_peers[piece]:
                self._piece_to_peers.pop(piece)
        except (KeyError, IndexError):
            pass
        except Exception as exc:
            logger.info(f'{exc=}'[:512])

        try:
            await self._results.put((piece, data))
        except Exception as exc:
            logger.info(f'{exc=}'[:512])
            raise Exception('put piece')

        try:
            if not self._missing_pieces:
                await self._results.close()
        except Exception as exc:
            logger.info(f'{exc=}'[:512])


async def download_from_peer(
        torrent, peer, info_hash, peer_id, pieces, max_requests,
        redis
):

    hex_info_hash = from_bytes_to_hex(info_hash)
    # max_requests = 500
    max_memory = int(redis.config_get('maxmemory')['maxmemory'])
    async with open_stream(peer) as stream:
        await stream.write(messages.Handshake(0, info_hash, peer_id))
        received = await stream.read_handshake()
        # logger.info(f'{received=}')
        if received.info_hash != info_hash:
            raise ValueError("Wrong 'info_hash'.")

        available = set()
        # Wait for the peer to tell us which pieces it has. This is not mandated
        # by the specification, but makes requesting pieces much easier.
        while True:

            received = await stream.read()
            if isinstance(received, messages.Have):
                available.add(pieces[received.index])
                break

            if isinstance(received, messages.Bitfield):
                for i in received.to_indices():
                    available.add(pieces[i])
                break

        state = State.CHOKED
        queue = Queue()
        while True:

            # await asyncio.sleep(0.1)

            try:
                piece_length = pieces[0].length
            except Exception as exc:
                # logger.info(f'piece_length {exc=}\n\n\n\n\n')
                piece_length = 20971520

            total = int(redis.memory_stats()['total.allocated'])
            # logger.info(f'{total=}, {max_memory=}')

            while total + piece_length * 50 > max_memory:
                logger.info(f'wait for free memory, {hex_info_hash=}')
                await asyncio.sleep(150+30+random.randint(10, 20))
                total = int(redis.memory_stats()['total.allocated'])

            if state is State.CHOKED:
                await stream.write(messages.Interested())
                state = State.INTERESTED
            elif state is State.UNCHOKED and queue.requested < max_requests:
                try:
                    block = queue.get_block()
                except IndexError:
                    try:
                        piece = torrent.get_piece(peer, available)
                    except IndexError as exc:
                        # log_stack.error('ch')
                        logger.info(f'{exc=} to passive, sleep')
                        state = State.PASSIVE
                        await asyncio.sleep(600)
                    else:
                        queue.add_piece(piece)
                else:
                    await stream.write(messages.Request.from_block(block))
            else:
                received = await stream.read()
                # logger.info(f'{type(received)=}')
                if isinstance(received, messages.Choke):
                    queue.reset_progress()
                    state = State.CHOKED
                elif isinstance(received, messages.Unchoke):
                    if state is not State.PASSIVE:
                        state = State.UNCHOKED
                elif isinstance(received, messages.Have):
                    # logger.info(f'{received.index=}, {pieces[received.index]}')
                    available.add(pieces[received.index])
                    if state is State.PASSIVE:
                        state = State.UNCHOKED
                elif isinstance(received, messages.Block):

                    # logger.info(f'{received.index=}, {pieces[received.index]}')
                    result = queue.put_block(
                        Block(
                            pieces[received.index],
                            received.begin,
                            len(received.data)),
                        received.data
                    )
                    # logger.info(f'1{result=}')
                    if result is not None:
                        await torrent.put_piece(peer, *result)

                    del result


async def download_from_peer_loop(
        torrent, trackers, info_hash, peer_id, pieces, max_requests,
        redis, peer=None,
        force_reconnect=False,
        # missing_pieces=None,
):

    while True:

        # if not missing_pieces:
        #     logger.info(f'no missing pieces')
        #     break

        if not peer:
            peer = await trackers.get_peer()

        # logger.info(f'{peer=}')
        try:
            torrent.peer_connected(peer)

            await download_from_peer(
                torrent, peer, info_hash, peer_id, pieces, max_requests,
                redis
            )
        except ConnectionRefusedError:
            if not force_reconnect:
                try:
                    trackers._seen_peers.remove(peer)
                except Exception:
                    pass

                try:
                    torrent.peer_disconnected(peer)
                except Exception:
                    pass
            pass
        except OSError:
            pass
        except Exception as exc:
            # TODO: DEBUG
            # log_stack.error('check')
            # logger.info(f'{exc=}')
            pass
        finally:
            try:
                trackers._seen_peers.remove(peer)
            except KeyError:
                pass
            except Exception as exc:
                logger.info(f'{exc=}')

            try:
                torrent.peer_disconnected(peer)
            except Exception as exc:
                logger.info(f'{exc=}')


@dataclasses.dataclass(frozen=True)
class Chunk:
    """The part of a `Piece` belonging to a single `File`.

    For transmission, files are concatenated and divided into pieces; a single
    piece can contain data belonging to multiple files. A `Chunk` represents a
    maximal contiguous slice of a piece belonging to a single file.
    """

    file: File
    piece: Piece
    begin: int  # Absolute offset.
    length: int

    async def aio_read(self, folder):
        async with aiofiles.open(folder / self.file.path, mode='rb') as f:
            await f.seek(self.begin - self.file.begin)
            return await f.read(self.length)

    # def read_to(self, folder, to):
    #     """Read the chunk's data from the file system."""
    #     with (folder / self.file.path).open("rb") as f:
    #         f.seek(self.begin - self.file.begin)
    #         to = f.read(self.length)
    #         return to

    def read(self, folder):
        """Read the chunk's data from the file system."""
        with (folder / self.file.path).open("rb") as f:
            f.seek(self.begin - self.file.begin)
            return f.read(self.length)

    def write(self, folder, data):
        """Write the chunk's data to the file system."""
        with (folder / self.file.path).open("rb+") as f:
            f.seek(self.begin - self.file.begin)
            begin = self.begin - self.piece.begin
            f.write(data[begin : begin + self.length])


def make_chunks(pieces, files):
    """Map each element of `pieces` to a list of its `Chunk`s."""
    result = {piece: [] for piece in pieces}
    i = 0
    j = 0
    begin = 0
    while i < len(files) and j < len(pieces):
        file = files[i]
        piece = pieces[j]
        file_end = file.begin + file.length
        piece_end = piece.begin + piece.length
        if file_end <= piece_end:
            end = file_end
            i += 1
        if piece_end <= file_end:
            end = piece_end
            j += 1
        result[piece].append(Chunk(file, piece, begin, end - begin))
        begin = end
    return result
