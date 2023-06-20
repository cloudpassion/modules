import socket
import aiohttp

from typing import TypeVar, Iterable
from os import getenv

from log import logger, log_stack
from .prepare import PrepareProxy


class ProxyParser(PrepareProxy):

    # inputs
    # proxy - proxy string, determinate all variables from this string
    # all data - ip, port, login, password, ssl_serts

    def __init__(self, proxy='',
                 ip=None, port=None,
                 login=None, password=None, scheme=None,
                 ssl_certs=None):

        self.proxy = None
        self.basic_auth = None
        self.aiogram_auth = None

        self.check = ''

        if not ip and not port and not proxy:
            self.from_input(ip, port, login, password, scheme, ssl_certs)

        else:

            if proxy and isinstance(proxy, str) and proxy.lower() != 'none':
                self.from_string(proxy, ssl_certs=ssl_certs)
            else:
                if isinstance(proxy, ProxyParser):
                    ip, port, login = proxy.ip, proxy.port, proxy.login
                    password, scheme, ssl_certs = proxy.password, proxy.scheme, proxy.ssl_certs

                self.from_input(
                    ip=ip, port=port,
                    login=login, password=password, scheme=scheme,
                    ssl_certs=ssl_certs
                )

            self.check_input()

        self.prepare()

    def check_scheme(self):
        if not self.scheme:
            if getenv('PROXY_PARSER_DEBUG'):
                raise NameError(f'{self.scheme} not support')
            else:
                raise NameError(f'this scheme not support')

        if any(
                s == self.scheme for s in (
                        'socks5', 'socks5-hostname', 'http', 'https'
                )):
            if 'hostname' in self.scheme:
                self.dns_resolve = True
            else:
                self.dns_resolve = False

            self.scheme = self.scheme.replace('-hostname', '')

    def check_ip(self):
        if not self.ip:
            raise BaseException(f'No ip')

        try:
            socket.inet_pton(socket.AF_INET, self.ip)
            self.ip_proto = socket.AF_INET
        except (socket.error, TypeError):
            try:
                socket.inet_pton(socket.AF_INET6, self.ip)
                self.ip_proto = socket.AF_INET6
                self.is_ip = True
            except (socket.error, TypeError):
                try:
                    self.ip = socket.getaddrinfo(
                        self.ip, None, socket.AF_INET)[0][4][0]
                    self.ip_proto = socket.AF_INET
                except socket.gaierror:
                    try:
                        self.ip = socket.getaddrinfo(
                            self.ip, None, socket.AF_INET6)[0][4][0]
                        self.ip_proto = socket.AF_INET6
                    except:
                        if getenv('PROXY_PARSER_DEBUG'):
                            raise socket.error(f'{self.ip=} not valid')
                        else:
                            raise socket.error(f'{self.ip=} not valid')

    def check_port(self):
        if self.port:
            if not (1 <= self.port <= 65535):
                if getenv('PROXY_PARSER_DEBUG'):
                    raise BaseException(f'{self.port} incorrect')
                else:
                    raise BaseException(f'port incorrect')
        else:
            raise BaseException(f'No port')

    def make_env(self):
        self.proxy = f'{self.scheme}://' \
                     f'{self.login + ":" if self.login else ""}' \
                     f'{self.password + "@" if self.password else ""}' \
                     f'{self.ip}:{self.port}'
        self.dns_proxy = f'{self.scheme + "-hostname" if self.dns_resolve else self.scheme}://' \
                          f'{self.login + ":" if self.login else ""}' \
                         f'{self.password + "@" if self.password else ""}' \
                         f'{self.ip}:{self.port}'

        self.basic_auth = aiohttp.BasicAuth(
            login=self.login, password=self.password
        ) if self.login and self.password else None

        self.aiogram_auth = self.basic_auth

    def check_input(self):

        if not self.ip and not self.port and not self.proxy:
            return

        self.check_scheme()
        self.check_ip()
        self.check_port()
        self.make_env()

        if self.check:
            func = getattr(self, self.check)
            if func:
                func()

    def from_string(self, proxy, ssl_certs):
        # allowed types
        # socks5, socks5-hostname, http, https ://
        # user:password@ip:port

        if 'ProxyParser' in proxy:
            self.check = proxy.split('[')[1].split(']')[0].split('.')[1]
            proxy = proxy.replace(f'[ProxyParser.{self.check}]', '')
            logger.critical(f'new proxy: {proxy}')

        scheme = proxy.split(':')[0]
        login = proxy.split(':')[1].split('/')[2] if '@' in proxy else None
        password = proxy.split(':')[2].split('@')[0] if '@' in proxy else None
        ip = proxy.replace(f'{scheme}://', '').replace(
            f'{login}:{password}' if login and password else '', ''
        ).split(':')[0]

        port = int(proxy.replace(f'{scheme}://', '').replace(
            f'{login}:{password}' if login and password else '', ''
        ).split(':')[1])

        self.from_input(ip, port, login, password, scheme, ssl_certs)

    def from_input(self, ip: str, port: TypeVar('A', str, int),
                   login: TypeVar('A', str, None),
                   password: TypeVar('A', str, None),
                   scheme: str,
                   ssl_certs: TypeVar('A', Iterable, None)
                   ):

        self.scheme = scheme
        self.ip = ip
        self.port = int(port) if port else port
        self.login = login
        self.password = password
        self.ssl_certs = ssl_certs

    def check_connect(self):
        try:
            sock = socket.socket(self.ip_proto, socket.SOCK_STREAM)
            connect = sock.connect((self.ip, self.port))
        except Exception as exc:
            if getenv('PROXY_PARSER_DEBUG'):
                raise type(exc)(f'{self.ip}:{self.port} cant connect')
            else:
                raise BaseException(f'cant connect')

    def from_list(self, proxies):
        ret_prx = []
        for prx in proxies:
            try:
                px = ProxyParser(proxy=prx)
                ret_prx.append(px)
            except BaseException:
                pass

        return ret_prx

    def best_of(self, proxies):
        proxy = ProxyParser(proxy=proxies[-1])
        return proxy

    def random(self, proxies):
        proxy = ProxyParser(proxy=proxies[-1])
        return proxy

    def full_check(self):
        return True
        # self.check_connect()


class old:

    def __init__(self, prx, login=None, password=None,):

        if isinstance(prx, Proxy):
            self.f = prx.f
            self.adr = prx.adr
            self.port = prx.port
            self.scheme = prx.scheme
            self.socks = prx.socks
            self.type = prx.type
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
                else:
                    self.type = socks.PROXY_TYPE_HTTP

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
