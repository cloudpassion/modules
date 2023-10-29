import sanic

from datetime import timedelta, datetime

from dht import DHTClient

from web.abstract import AbstractServer


class DHTWeb(
    AbstractServer,
):

    dht_servers: dict
    announce_timeout = timedelta(minutes=25)

    async def dht_announce_semaphore(self, request):
        return await self.dht_announce(request)

    async def dht_announce(self, request):

        pass

    async def load_dht_routes(self):
        app = self.app

        @app.route(
            'adht'
        )
        async def dht_announce(request: sanic.Request):
            return await self.dht_announce_semaphore()

    async def run_dht_clients(self):
        # pfru
        pfru = DHTClient(25431, hint='pfru')
        #await pfru.run()

        # pfvps
        # pfvps = DHTClient(25432, hint='pfvps')
        # await pfvps.run()
        #
        # self.dht_servers = {
        #     'pfru': pfru,
        #     'pfvps': pfvps
        # }

        #await pfru.announce(
        #    'e39b176c6ab63f090570d25423c5fc956d048c7a', 3153
        #)
