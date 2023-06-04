import random

try:
    from log import logger
except ImportError:
    from ..log import logger

try:
    from aiosocksy import Socks5Auth
    from aiosocksy.connector import ProxyClientRequest
except ImportError:
    logger.info(f'need install aiosocksy for using Socks5Auth, ProxyClientRequest')

try:
    from aiohttp_socks import ProxyConnector, ProxyType
except ImportError:
    logger.info(f'need install aiohttp_socks for ProxyConnecton, ProxyType')

try:
    import socks
except ImportError:
    logger.info(f'need install requests[socks] for socks')


class Proxy:
    def __init__(self, prx, login=None, password=None):

        if isinstance(prx, Proxy):
            self.f = prx.f
            self.adr = prx.adr
            self.port = prx.port
            self.scheme = prx.scheme
            self.socks = prx.socks
            self.type = prx.type
            self.aio_type = None
            self.auth = prx.auth
            self.str = prx.str
            self.aio_auth = prx.aio_auth
            self.aio_str = prx.aio_str
            self.login = prx.login
            self.password = prx.password
        else:
            if not prx:
                self.adr = None
                self.port = None
                self.scheme = None
                self.socks = None
                self.type = None
                self.aio_type = None
                self.auth = None
                self.str = None
                self.aio_auth = None
                self.aio_str = None
                self.login = None
                self.password = None
                self.f = None
            else:
                self.f = prx
                self.scheme = prx.split(':')[0]
                self.socks = False
                if 'socks' in self.scheme:
                    self.socks = True
                    self.type = socks.PROXY_TYPE_SOCKS5
                    self.aio_type = ProxyType.SOCKS5
                else:
                    self.type = socks.PROXY_TYPE_HTTP
                    self.aio_type = socks.PROXY_TYPE_HTTP

                self.adr = prx.split('/')[2].split(':')[0]
                self.port = int(prx.split(':')[2])
                self.login = login
                self.password = password
                self.auth, self.aio_auth = None, None
                self.aio_str = self.scheme+'://'+self.adr+':'+str(self.port)
                if not login:
                    self.str = self.scheme+'://'+self.adr+':'+str(self.port)
                else:
                    self.str = self.scheme + '://' + self.login + ':' + \
                               self.password + '@' + self.adr + ':' + str(self.port)
                    self.auth = True
                    self.aio_auth = Socks5Auth(login=self.login, password=self.password)


class Proxies:

    def __init__(self, _config):

        self.proxies = []
        self.tproxies = []
        self.used_proxies = set()

        self.prx_n = 0
        while True:
            try:
                self.proxies.append(Proxy(_config['network']['proxy_address'+str(self.prx_n)]))
            except:
                break
            self.prx_n += 1

        self.tprx_n = 0
        while True:
            try:
                self.tproxies.append(Proxy(_config['network']['tproxy_address'+str(self.tprx_n)]))
            except:
                break
            self.tprx_n += 1
        self.random()

    def random(self):
        if self.proxies:
            self.rnd = self.proxies[random.randint(0, self.prx_n - 1)]
        else:
            self.rnd = None
        if self.tproxies:
            self.trnd = self.tproxies[random.randint(0, self.tprx_n - 1)]
        else:
            self.trnd = None

