# import time
# import math
# import asyncio
# import random
# import socket
# import aiohttp
# import urllib.parse
# import bencodepy
#
# from progress.bar import Bar
#
# from krbt.client import (
#     Client as DefaultClient,
#     DownloadManager as DefaultDownloadManager,
#     Block, Piece
# )
# from krbt.utils import generate_peer_id
# from krbt.message import REQUEST_SIZE
# from krbt.protocol import (
#     PeerConnection as DefaultPeerConnection,
#     PeerStreamIterator as DefaultPeerStreamIterator,
#     PeerState,
#     NotInterestedMessage,
#     ChokeMessage, UnchokeMessage, HaveMessage,
#     PieceMessage, CancelMessage, BitFieldMessage, RequestMessage,
#
# )
# from krbt.tracker import HTTPTracker as DefaultHTTPTracker, TrackerResponse, _decode_port
# from krbt.torrent_parser import parse
#
#
# from log import logger
#
#
# class PeerStreamIterator(DefaultPeerStreamIterator):
#     def __aiter__(self):
#         return self
#
#
# class PeerConnection(DefaultPeerConnection):
#     pass
#
#     async def handle_message(self, buffer):
#         if not buffer:
#             await self.send_interested()
#
#         async for message in PeerStreamIterator(self.reader, buffer):
#             if PeerState.Stopped.value in self.current_state:
#                 break
#
#             if isinstance(message, NotInterestedMessage):
#                 try:
#                     logger.debug('Remove interested state')
#                     self.current_state.remove(PeerState.Interested.value)
#                 except ValueError:
#                     pass
#             elif isinstance(message, ChokeMessage):
#                 logger.debug('Received choke message')
#                 self.current_state.append(PeerState.Choked.value)
#             elif isinstance(message, UnchokeMessage):
#                 logger.debug('Received unchoke message')
#                 try:
#                     logger.debug('Remove choked state')
#                     self.current_state.remove(PeerState.Choked.value)
#                 except ValueError:
#                     pass
#             elif isinstance(message, HaveMessage):
#                 self.download_manager.update_peer(self.remote_id,
#                                                   message.index)
#                 logger.debug('Received have message')
#             elif isinstance(message, BitFieldMessage):
#                 logger.info('Received bit field message: {}'.format(message))
#                 if PeerState.Interested.value not in self.current_state:
#                     await self.send_interested()
#                     logger.debug('Sending interested')
#                 self.download_manager.add_peer(peer_id=self.remote_id,
#                                                bitfield=message.bitfield)
#             elif isinstance(message, PieceMessage):
#                 # logger.debug('Received piece message')
#                 self.current_state.remove(PeerState.PendingRequest.value)
#                 self.on_block_complete(peer_id=self.remote_id,
#                                        piece_index=message.index,
#                                        block_offset=message.begin,
#                                        data=message.block)
#             elif isinstance(message, RequestMessage):
#                 # TODO: Implement uploading data
#                 pass
#             elif isinstance(message, CancelMessage):
#                 # TODO: Implement cancel data
#                 pass
#
#             await self.send_next_message()
#
#         self.cancel()
#         logger.info(f'end')
#
#
# class DownloadManager(DefaultDownloadManager):
#
#     def __init__(self, torrent, savedir):
#         self.torrent = torrent
#         self.total_pieces = len(self.torrent.info.pieces)
#         self.peers = {}
#         # TODO: Come up with different data structure to store
#         # states of different pieces and blocks. Probably dict or set?
#         self.pending_blocks = []
#         self.ongoing_pieces = []
#         self.have_pieces = []
#         self.missing_pieces = self.make_pieces()
#         self.max_pending_time = 300 * 1000 # Seconds
#         self.progress_bar = Bar('Downloading', max=self.total_pieces)
#         # if savedir == '.':
#         #     name = self.torrent.name
#         # else:
#         #     name = os.path.join(savedir, self.torrent.name)
#         # self.fd = os.open(name, os.O_RDWR | os.O_CREAT)
#
#     def _write(self, piece):
#         pass
#         # pos = piece.index * self.torrent.info.piece_length
#         # os.lseek(self.fd, pos, os.SEEK_SET)
#         # os.write(self.fd, piece.data)
#
#     def close(self):
#         pass
#
#     def make_pieces(self):
#         total_pieces = len(self.torrent.info.pieces)
#         total_piece_blocks = math.ceil(
#             self.torrent.info.piece_length / REQUEST_SIZE)
#         pieces = []
#         for index, hash_value in enumerate(self.torrent.info.pieces):
#             if index < (total_pieces - 1):
#                 blocks = [Block(index, offset * REQUEST_SIZE,
#                                 REQUEST_SIZE)
#                           for offset in range(total_piece_blocks)]
#             else:
#                 # logger.info(f'{self.torrent.info=}')
#                 # logger.info(f'{self.torrent.info.length=}')
#                 # logger.info(f'{self.torrent.info.piece_length=}')
#                 # last_length = self.torrent.info.length % self.torrent.info.piece_length
#                 last_length = (
#                                       self.torrent.info.piece_length * self.total_pieces
#                               ) % self.torrent.info.piece_length
#                 num_blocks = math.ceil(last_length / REQUEST_SIZE)
#                 blocks = [Block(index, offset * REQUEST_SIZE, REQUEST_SIZE)
#                           for offset in range(num_blocks)]
#
#                 if last_length % REQUEST_SIZE > 0:
#                     last_block = blocks[-1]
#                     last_block.length = last_length % REQUEST_SIZE
#                     blocks[-1] = last_block
#             pieces.append(Piece(index, blocks, hash_value))
#         logger.debug('Completed calculating pieces')
#         return pieces
#
#
# class HTTPTracker(DefaultHTTPTracker):
#     pass
#
#     def parse_tracker_response(self, content):
#         resp = bencodepy.decode(content)
#         logger.info(f'{resp=}')
#         if b'failure reason' in resp:
#             logger.info(f'fail')
#             return
#
#         split_peers = [resp[b'peers'][i:i+6]
#                        for i in range(0, len(resp[b'peers']), 6)]
#
#         peers = [(socket.inet_ntoa(p[:4]), _decode_port(p[4:]))
#                  for p in split_peers]
#         return TrackerResponse(resp[b'complete'], resp.get(b'crypto_flags'),
#                                resp.get(b'incomplete'), resp.get(b'interval'),
#                                peers)
#
#     async def announce(self):
#         """
#         """
#         logger.debug('announce')
#         params = self.build_params_for_announce()
#         # logger.info(f'{params=}')
#
#         url = urllib.parse.urlparse(self.url)
#         # q = urllib.parse.parse_qs(url.query)
#         # q.update(params)
#         # path = url._replace(scheme="", netloc="", query=urllib.parse.urlencode(q)).geturl()
#         # # logger.info(f'{path=}')
#         # # logger.info(f'{url=}')
#         # full_url = f'{url.scheme}://{url.netloc}{path}'
#         # logger.info(f'{full_url=}')
#         # # quit()
#
#         parse = urllib.parse.urlparse(url.query)
#         q = urllib.parse.parse_qs('')
#         q.update(params)
#         # logger.info(f'{q=}')
#         # q['peer_id'] = q['peer_id'].decode('utf8')
#         # logger.info(f'{q=}')
#         # if 'port' in q:
#         #     q['port'] = random.randint(1000, 65535)
#
#         query = urllib.parse.urlencode(q)
#         e = '&' if parse.path else ''
#         query = f'{parse.path}{e}{query}'
#         path = url._replace(
#             scheme="", netloc="",
#             query=query,
#         ).geturl()
#
#         full_url = f'{url.scheme}://{url.netloc}{path}'
#         logger.info(f'{full_url=}')
#
#         if 'tor4me' in full_url:
#             proxies = {
#                 'http': 'http://192.168.55.232:53139',
#                 'https': 'http://192.168.55.232:53139'
#             }
#             proxy = 'http://192.168.55.232:53139'
#         else:
#             proxies = None
#             proxy = None
#
#         try:
#             async with aiohttp.ClientSession(
#             ) as session:
#                 async with session.get(
#                     f'{full_url}',
#                     proxy=proxy,
#                     #params=params
#                 ) as resp:
#                     if resp.status == 200:
#                         content = await resp.read()
#                         return self.parse_tracker_response(content)
#         except Exception as exc:
#             logger.info(f'{exc=}')
#
#         try:
#             await session.close()
#         except Exception as exc:
#             logger.info(f'{exc=}')
#
#         try:
#             session.close()
#         except Exception as exc:
#             logger.info(f'{exc=}')
#
#
# class Client(DefaultClient):
#
#     def __init__(self):
#         super.__init__()
#         self.trackers = []
#
#     async def _get_peers(self, torrent):
#         peers = []
#         trakers = [x[0] for x in torrent.announce_list]
#
#         for tr in [torrent.announce, *trakers]:
#             logger.info(f'{tr=}')
#             try:
#                 tracker = HTTPTracker(url=tr,
#                                       size=torrent.info.length,
#                                       info_hash=torrent.hash)
#             except Exception as exc:
#                 logger.info(f'{exc=}')
#                 continue
#
#             self.trackers.append(tracker)
#             resp = await tracker.announce()
#             if not resp:
#                 continue
#
#             peers.extend(resp.peers)
#
#         return peers
#
#     async def download(self, path, savedir):
#         torrent = parse(path)
#         torrent.print_all_info()
#
#         if torrent.announce.startswith(b'http'):
#             # peers = await self._get_peers(torrent)
#             peers = [('94.41.237.148', 22764), ('31.202.45.165', 39097), ('95.25.149.248', 34553),
#                      ('91.219.83.5', 56974), ('62.221.66.15', 16911), ('193.218.141.19', 10643),
#                      ('118.93.165.31', 12345), ('212.142.66.38', 51876), ('188.119.113.97', 51198),
#                      ('37.150.53.98', 6881), ('94.41.237.148', 22764), ('31.202.45.165', 39097),
#                      ('95.25.149.248', 34553), ('91.219.83.5', 56974), ('62.221.66.15', 16911),
#                      ('193.218.141.19', 10643), ('118.93.165.31', 12345), ('212.142.66.38', 51876),
#                      ('188.119.113.97', 51198), ('37.150.53.98', 6881)]
#
#             peers = [('192.168.55.59', 51198), ]
#
#             logger.info(f'{peers=}')
#             # self.tracker = tracker
#             # resp = await tracker.announce()
#             self.previous = time.time()
#             self.download_manager = DownloadManager(torrent, savedir)
#             for peer in peers:
#                 self.available_peers.put_nowait(peer)
#
#             self.peers = [PeerConnection(
#                 info_hash=torrent.hash,
#                 peer_id=generate_peer_id(),
#                 available_peers=self.available_peers,
#                 download_manager=self.download_manager,
#                 on_block_complete=self.on_block_complete)
#                 for _ in range(2)]
#
#             await self.monitor()
#
#         elif torrent.announce.startswith(b'udp'):
#             logger.info("UDP tracker isn't supported")
#             exit(1)
#
#     async def monitor(self):
#         # Interval in seconds
#         interval = 1 * 60
#
#         while True:
#             if self.download_manager.complete:
#                 logger.info('Download complete, exiting...')
#                 break
#             elif self.abort:
#                 logger.info('Aborting download...')
#                 break
#
#             current = time.time()
#             if self.previous + interval < current:
#                 for tracker in self.trackers:
#                     response = await tracker.connect(
#                         first=self.previous if self.previous else False,
#                         uploaded=self.download_manager.bytes_uploaded,
#                         downloaded=self.download_manager.bytes_downloaded)
#                     logger.debug('Tracker response: {}'.format(response))
#                     if response:
#                         self.previous = current
#                         interval = response.interval
#                         self._empty_queue()
#                         for peer in response.peers:
#                             self.available_peers.put_nowait(peer)
#             else:
#                 await asyncio.sleep(0.1)
#         self.stop()
