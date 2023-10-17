import binascii
import os
import time
import secrets
import asyncio
import functools
import random
import urllib.parse
import dataclasses
import http.client

from typing import Any, List

from surge.tracker import (
    Trackers as SurgeTrackers,
    # request_peers_udp,
    create_udp_tracker_protocol,
    UDPConnectRequest, UDPAnnounceRequest, UDPAnnounceResponse, UDPConnectResponse,
    Parameters as DefaultParameters,
    Result as DefaultResult,
    Peer,
    _parse_peers,
    Result
)
import surge.bencoding as bencoding

from config import secrets as config_secrets
from log import logger, log_stack

from ..encoding.resurge import decode


# @dataclasses.dataclass
# class Parameters:
#     info_hash: bytes
#     peer_id: str
#     port: int = 0
#     uploaded: int = 0
#     downloaded: int = 0
#     # This is initialized to 0 because we also need to connect to the tracker
#     # before downloading the metadata.
#     left: int = 0
#     compact: int = 1
#     # pk: str = ''
#     # uk: str = ''
#     # passkey: str = ''


@dataclasses.dataclass
class Result:
    interval: int
    peers: List[Peer]

    @classmethod
    def from_bytes(cls, interval, raw_peers):
        return cls(interval, _parse_peers(raw_peers))

    @classmethod
    def from_dict(cls, resp):
        if isinstance(resp[b"peers"], list):
            # Dictionary model, as defined in BEP 3.
            peers = [Peer.from_dict(d) for d in resp[b"peers"]]
            # logger.info(f'{peers=}')
        else:
            # Binary model ("compact format") from BEP 23.
            peers = _parse_peers(resp[b"peers"])
            # logger.info(f'{peers=}')
        return cls(resp[b"interval"], peers)


def get(url, parameters):
    # I'm using `http.client` instead of the `urllib.request` wrapper here
    # because the latter is not thread-safe.
    # logger.info(f'{url=}')

    # def_q = urllib.parse.urlparse(url.query)
    # logger.info(f'{def_q=}')
    # q = urllib.parse.parse_qs(url.query)
    parse = urllib.parse.urlparse(url.query)
    q = urllib.parse.parse_qs('')
    q.update(dataclasses.asdict(parameters))
    # logger.info(f'{q=}')
    q['peer_id'] = q['peer_id'].decode('utf8')
    # logger.info(f'{q=}')
    if 'port' in q:
        q['port'] = random.randint(1000, 65535)

    query = urllib.parse.urlencode(q)
    e = '&' if parse.path else ''
    query = f'{parse.path}{e}{query}'
    path = url._replace(
        scheme="", netloc="",
        query=query,
    ).geturl()

    # pt = ''
    # for k in def_q.keys():
    #     logger.info(f'{k=}')
    #     if k not in q:
    #         pt += f'{k}={def_q[k][0]}'
    #
    # split = url.path.split('?')[0]
    # logger.info(f'{split=}')
    # path.replace('?', '').replace(split, f'{split}?{pt}')
    # logger.info(f'{path=}')

    if not url.netloc.endswith('.local'):

        # logger.info(f'using proxy {secrets.proxy.http.ip}{secrets.proxy.http.port}')
        if url.scheme == "http":
            http_connection = http.client.HTTPConnection
        elif url.scheme == 'https':
            http_connection = http.client.HTTPSConnection
        else:
            raise ValueError("Wrong scheme.")

        conn = http_connection(
            config_secrets.proxy.http.ip, port=config_secrets.proxy.http.port,
            timeout=30,
        )
        conn.set_tunnel(
            url.netloc,
        )
    else:
        if url.scheme == "http":
            conn = http.client.HTTPConnection(
                url.netloc, timeout=30)
        elif url.scheme == "https":
            conn = http.client.HTTPSConnection(url.netloc, timeout=30)
        else:
            raise ValueError("Wrong scheme.")

    try:
        # logger.info(f'{url=}')
        try:
            conn.request(
                "GET", path,
                headers={
                    'Host': url.netloc,
                    'User-Agent': 'surge/7.85.0'
                }
            )
            resp = conn.getresponse().read()
        except Exception:
            resp = bencoding.encode(b'failure reason')

        # logger.info(f'{url.netloc=}: {resp=}')
        return resp
    finally:
        conn.close()


async def request_peers_http(root, url, parameters):
    loop = asyncio.get_running_loop()
    while True:
        # I'm running the synchronous HTTP client from the standard library
        # in a separate thread here because HTTP requests only happen
        # sporadically and `aiohttp` is a hefty dependency.
        try:
            d = decode(
                await loop.run_in_executor(
                    None, functools.partial(get, url, parameters)
                )
            )
        except Exception:
            await asyncio.sleep(200+random.randint(50, 150))
            continue

        # logger.info(f'{d=}')
        if b"failure reason" in d:
            await asyncio.sleep(300)
            continue
            # raise ConnectionError(d[b"failure reason"].decode())
        result = Result.from_dict(d)
        for peer in result.peers:
            # logger.info(f'{peer=}')
            await root.put_peer(peer)
        await asyncio.sleep(120)
        #result.interval)


async def request_peers_udp(root, url, parameters):
    while True:
        try:
            async with create_udp_tracker_protocol(url) as protocol:
                connected = False
                for n in range(9):
                    timeout = 15 * 2**n
                    if not connected:
                        transaction_id = secrets.token_bytes(4)
                        protocol.write(UDPConnectRequest(transaction_id))
                        try:
                            received = await asyncio.wait_for(protocol.read(), timeout)
                        except asyncio.TimeoutError:
                            continue
                        except (ConnectionRefusedError, ValueError):
                            await asyncio.sleep(300)
                            continue

                        if isinstance(received, UDPConnectResponse):
                            connected = True
                            connection_id = received.connection_id
                            connection_time = time.monotonic()
                    if connected:
                        protocol.write(
                            UDPAnnounceRequest(
                                transaction_id, connection_id, parameters
                            )
                        )
                        try:
                            received = await asyncio.wait_for(protocol.read(), timeout)
                        except asyncio.TimeoutError:
                            continue
                        if isinstance(received, UDPAnnounceResponse):
                            result = received.result
                            break
                        if time.monotonic() - connection_time >= 60:
                            connected = False
                else:
                    raise ConnectionError("Maximal number of retries reached.")
        except Exception as exc:
            # log_stack.error('ch')
            # logger.info(f'udp_{exc=}')
            await asyncio.sleep(60)
            continue

        for peer in result.peers:
            await root.put_peer(peer)

        await asyncio.sleep(result.interval)


async def request_peers(root, url, parameters):
    try:
        if url.scheme in ("http", "https"):
            return await request_peers_http(root, url, parameters)
        if url.scheme == "udp":
            return await request_peers_udp(root, url, parameters)
        raise ValueError("Invalid scheme.")
    # except ValueError:
    #     root.tracker_disconnected(url)
    finally:
        root.tracker_disconnected(url)


class Trackers(
    SurgeTrackers,
):

    # def __init__(self, info_hash, peer_id, announce_list, max_peers):
    #     super().__init__(info_hash, peer_id, announce_list, max_peers)
    #     self._parameters = Parameters(info_hash, peer_id)

    async def __aenter__(self):
        for url in map(urllib.parse.urlparse, self._announce_list):
            self._trackers[url] = asyncio.create_task(
                request_peers(self, url, self._parameters)
            )
        return self
