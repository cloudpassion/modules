from atiny.http.aio import MyHttp

from config import settings, secrets


class Http:

    host = 'kinozal.tv'
    proxy = settings.http.proxy.address
    proxy_ssl_cert = settings.http.proxy.ssl_cert
    headers: dict = {}

    def load_cookies(self):
        self.headers.update(
            {
                'cookie': secrets.cookie
            }
        )

    async def get(self, url, headers=None):

        http = MyHttp(
            proxy=self.proxy, ssl_cert=self.proxy_ssl_cert,
            save_cache=settings.http.cache.save,
            load_cache=settings.http.cache.load,
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
