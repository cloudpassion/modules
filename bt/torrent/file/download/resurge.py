import os
import aiofiles
import contextlib
import asyncio
import collections
import dataclasses
import random

from surge.stream import Stream as DefaultStream

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
from ...stuff.exceptions import NotHaveTorrent
from ...stuff.check import redis_memory_wait

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
    def __init__(self, pieces, missing_pieces, results):
        # self._missing_pieces = set(missing_pieces)
        self._missing_pieces = missing_pieces
        self._peer_to_pieces = {}
        self._piece_to_peers = collections.defaultdict(set)
        self._pieces = pieces
        self._results = results
        # This check is necessary because `put_piece` is never called if there
        # are no pieces to download.
        if not self._missing_pieces:
            self._results.close_nowait()

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
            else:
                for peer in self._peer_to_pieces.keys():
                    try:
                        self._peer_to_pieces[peer].remove(piece)
                    except (KeyError, IndexError) as exc:
                        pass

                    try:
                        self._piece_to_peers[piece].remove(peer)
                    except (KeyError, IndexError) as exc:
                        pass

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

    def get_piece(self, peer, available):
        """Return a piece to download next.

        Raise `IndexError` if there are no additional pieces to download.
        """
        # logger.info(f'{peer=}')
        pool = self._missing_pieces & (available - self._peer_to_pieces[peer])
        # logger.info(f'{pool=}')
        piece = random.choice(tuple(pool - set(self._piece_to_peers) or pool))
        # logger.info(f'{piece=}')
        self._peer_to_pieces[peer].add(piece)
        # logger.info(f'2')
        self._piece_to_peers[piece].add(peer)
        # logger.info(f'3')
        return piece


class Stream(DefaultStream):

    # TODO: check if chunk have zero size
    # what coming in prefix
    async def read(self):
        prefix = await self._reader.readexactly(4)
        data = await self._reader.readexactly(int.from_bytes(prefix, "big"))
        return messages.parse(prefix + data)


@contextlib.asynccontextmanager
async def open_stream(peer):
    reader, writer = await asyncio.open_connection(peer.address, peer.port)
    try:
        yield Stream(reader, writer)
    finally:
        writer.close()
        await writer.wait_closed()


async def download_from_peer(
        torrent, peer, info_hash, peer_id, pieces, max_requests,
        redis, read_delay=0
):

    # only for redis memory monitoring
    try:
        piece_length = pieces[0].length
    except (KeyError, AttributeError) as exc:
        # logger.info(f'piece_length {exc=}\n\n\n\n\n')
        piece_length = 20971520

    hex_info_hash = from_bytes_to_hex(info_hash)
    # max_requests = 500
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

            await redis_memory_wait(
                r=redis,
                more_total=piece_length*50,
                info=hex_info_hash,
            )

            await asyncio.sleep(read_delay)
            received = await stream.read()
            if isinstance(received, messages.Have):
                # logger.info(f'{received.index=}, {pieces=}')
                available.add(pieces[received.index])
                logger.info(f'1.{len(available)=}, {hex_info_hash=}')

            elif isinstance(received, messages.Bitfield):
                for i in received.to_indices():
                    # logger.info(f'{i=}, {pieces=}')
                    available.add(pieces[i])
                logger.info(f'2.{len(available)=}, {hex_info_hash=}')

            else:
                logger.info(f'3.sleep.{received=}, {len(available)=}, {hex_info_hash=}')
                await asyncio.sleep(30)
                continue

            if available:
                await asyncio.sleep(1)
                break

            if not available:
                logger.info(f'{received=}, {hex_info_hash=}')
                await asyncio.sleep(1)
                raise NotHaveTorrent

        state = State.CHOKED
        queue = Queue()
        passive_try = 0
        while True:

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
                        logger.info(f'{passive_try=}, {peer=},'
                                    f' {torrent._peer_to_pieces=}, {torrent._piece_to_peers=}'
                                    f' {exc=} to passive, sleep, {hex_info_hash=}')
                        passive_try += 1
                        if passive_try >= 10:
                            logger.info(f'raise, {passive_try=}, {hex_info_hash=}')
                            raise Exception(f'passive exc, {hex_info_hash=}')
                        # log_stack.error('ch')
                        state = State.PASSIVE
                        await asyncio.sleep(240)
                    else:
                        # logger.info(f'add queue, {piece=}, {hex_info_hash=}')
                        queue.add_piece(piece)
                else:
                    await stream.write(messages.Request.from_block(block))
            else:

                await redis_memory_wait(
                    r=redis,
                    more_total=piece_length*50,
                    info=hex_info_hash,
                )

                await asyncio.sleep(read_delay)
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
    read_delay = 0
    hex_info_hash = from_bytes_to_hex(info_hash)
    while True:

        # if not missing_pieces:
        #     logger.info(f'no missing pieces')
        #     break

        if not peer:
            peer = await trackers.get_peer()

        # logger.info(f'{peer=}')

        torrent.peer_connected(peer)

        try:
            await download_from_peer(
                torrent, peer, info_hash, peer_id, pieces, max_requests,
                redis, read_delay=read_delay
            )
        except ConnectionRefusedError as exc:
            if not force_reconnect:
                try:
                    trackers._seen_peers.remove(peer)
                except Exception:
                    pass

                try:
                    torrent.peer_disconnected(peer)
                except Exception:
                    pass

            logger.info(f'sleep1: {hex_info_hash=}, {exc=}')
            await asyncio.sleep(60+random.randint(150, 300))
        except OSError as exc:
            read_delay += 0.1
            log_stack.error(f'sleep2 {hex_info_hash=}')
            logger.info(f'sleep2: {hex_info_hash=}, {exc=}')
            # await asyncio.sleep(60+random.randint(150, 300))
        except NotHaveTorrent:
            logger.info(f'{peer=} not have {hex_info_hash=}')
            await asyncio.sleep(600)
        except asyncio.IncompleteReadError as exc:
            await asyncio.sleep(300+random.randint(150, 300))
        except Exception as exc:
            pass
            # TODO: DEBUG
            # log_stack.error('check')
            # logger.info(f'sl')
            logger.info(f'sleep3: {hex_info_hash=} {exc=}')
            await asyncio.sleep(60+random.randint(150, 300))
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
