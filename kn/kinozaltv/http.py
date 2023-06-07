from atiny.http import MyHttp

from log import logger
from config import settings, secrets


class Http:

    host = 'kinozal.tv'
    try:
        proxy = secrets.http.proxy.address
        proxy_ssl_cert = secrets.http.proxy.ssl_cert
    except AttributeError:
        proxy = None
        proxy_ssl_cert = None

    headers: dict = {}

    def load_cookies(self):
        self.headers.update(
            {
                'cookie': secrets.cookie
            }
        )

    async def get(self, url, headers=None):

        try:
            save_cache = settings.http.cache.save
        except AttributeError:
            save_cache = False

        try:
            load_cache = settings.http.cache.load
        except AttributeError:
            load_cache = False

        http = MyHttp(
            proxy=self.proxy, ssl_cert=self.proxy_ssl_cert,
            save_cache=save_cache,
            load_cache=load_cache,
            save_headers=False,
            log=False,
        )

        if headers:
            self.headers.update(
                headers
            )

        resp = await http.get(
            url, headers=self.headers.copy()
        )

        return resp
