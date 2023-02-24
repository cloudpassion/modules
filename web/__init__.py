import redis

from sanic import Sanic

from .default import DefaultHandler
from .kinozal.tor2me import Tor2Me
from .kinozal.info import Info
from dht.web import DHTWeb


class WEB(
    DefaultHandler,
    Tor2Me,
    Info,
    DHTWeb,
):

    def __init__(self):
        app = Sanic("web_server")
        app.config.REQUEST_TIMEOUT = 480
        app.config.RESPONSE_TIMEOUT = 480

        self.app = app

        self.io_media = {}

    async def initialize(self):

        await self.run_dht_clients()
        await self.load_dht_routes()

        self.redis_conn = redis.Redis('localhost')
        await self.load_default()
        await self.load_tor2me()
        await self.load_info()

