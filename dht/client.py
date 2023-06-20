import asyncio
import string
import random

from aiobtdht import DHT
from aioudp import UDPServer

from log import logger


class DHTClient:

    dht: DHT

    initial_nodes = [
        ("67.215.246.10", 6881),  # router.bittorrent.com
        ("87.98.162.88", 6881),  # dht.transmissionbt.com
        ("82.221.103.244", 6881)  # router.utorrent.com
    ]

    def __init__(self, listen_port, auto_random=True, hint=''):

        self.hint = hint

        port_available = self.check_port(listen_port)
        if not port_available and not auto_random:
            raise Exception

        if not port_available and auto_random:
            while not port_available:
                listen_port = self.get_random_port()
                port_available = self.check_port(listen_port)

        self.listen_port = listen_port

    def get_random_port(self):
        return 12312

    def check_port(self, port):
        return True

    async def run(self):

        udp = UDPServer()
        udp.run("0.0.0.0", self.listen_port, asyncio.get_event_loop())

        local_id = f'0x' + ''.join(
            random.choice(
                'ABCDEF' + string.digits
            ) for _ in range(40)
        )

        local_id = '0x54A10C9B159FC0FBBF6A39029BCEF406904019E0'
        self.dht = DHT(
            int(local_id, 16),
            server=udp, loop=asyncio.get_event_loop()
        )

        await self.dht.bootstrap(self.initial_nodes)

        logger.info(f'listen to {self.hint} on {self.listen_port}')

    async def search_peers(self, info_hash):
        peers = await self.dht[
            bytes.fromhex(info_hash)
        ]
        return peers

    async def announce(self, info_hash, port):
        await self.dht.announce(
            bytes.fromhex(info_hash),
            int(port)
        )
        await self.check(info_hash, port)

    async def check(self, info_hash, port):
        peers = await self.search_peers(info_hash)
        logger.info(f'{peers=}')
        for _hash in [
            "8df9e68813c4232db0506c897ae4c210daa98250",
            'ECB3E22E1DC0AA078B48B7323AEBBA827AD9BD80',
        ]:
            peers = await self.dht[
                bytes.fromhex(_hash)
            ]
            logger.info(f'{peers=}')

        for peer in peers:
            ip, peer_port = peer
            if peer_port == port:
                logger.info(f'{ip}, {port}')


