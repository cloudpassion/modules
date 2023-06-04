from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
from poplib import POP3, POP3_SSL, POP3_PORT, POP3_SSL_PORT
from smtplib import SMTP, SMTP_SSL, SMTP_PORT, SMTP_SSL_PORT

try:
    from log import logger
except ImportError:
    from ...log import logger

try:
    from socks import (
        create_connection,
        PROXY_TYPE_HTTP, PROXY_TYPE_SOCKS4, PROXY_TYPE_SOCKS5
    )
except ImportError:
    logger.info(f'need to install PySocks for mail proxy works')

import socket
import sys
from urllib.parse import urlparse
from collections import namedtuple

# https://codereview.stackexchange.com/questions/253311/universal-class-for-proxifying-poplib-imaplib-and-smtplib-lame-inheritance-or


def imap_before_connection(self, *args):
    sys.audit("imaplib.open", self, self.host, self.port)


def smtp_before_connection(self, host, port):
    if self.debuglevel > 0:
        self._print_debug('connect: to', (host, port), self.source_address)


def pop_before_connection(*args):
    pass


DEFAULT_SETTINGS = {
    POP3_SSL: (POP3_SSL_PORT, pop_before_connection),
    IMAP4_SSL: (IMAP4_SSL_PORT, imap_before_connection),
    SMTP_SSL: (SMTP_SSL_PORT, smtp_before_connection),
    POP3: (POP3_PORT, pop_before_connection),
    IMAP4: (IMAP4_PORT, imap_before_connection),
    SMTP: (SMTP_PORT, smtp_before_connection)
}


def proxify(base_type):
    for type_, (default_port, before_connection) in DEFAULT_SETTINGS.items():
        if issubclass(base_type, type_):
            break
    else:
        raise TypeError(f"Can't proxify {base_type}")

    class Proxified(base_type):
        Proxy = namedtuple(
            "Proxy",
            ("host", "port", "username", "password", "proxy_type", "rdns")
        )
        on_before_connection = before_connection

        @staticmethod
        def parse_proxy_string(proxy_string):
            if not proxy_string:
                return None

            parsed = urlparse(proxy_string)
            _scheme = parsed.scheme.lower()
            if _scheme in {"http", "https"}:
                proxy_type, remote_dns = PROXY_TYPE_HTTP, True
            elif _scheme in {"socks4", "socks4a"}:
                proxy_type, remote_dns = PROXY_TYPE_SOCKS4, _scheme.endswith("a")
            elif _scheme in {"socks5", "socks5h"}:
                proxy_type, remote_dns = PROXY_TYPE_SOCKS5, _scheme.endswith("h")
            else:
                raise ValueError(f'"{_scheme}" is not supported proxy type')

            return Proxified.Proxy(parsed.hostname, parsed.port, parsed.username, parsed.password,
                                   proxy_type, remote_dns)

        def __init__(self, host="", port=default_port, *args, **kwargs):
            self.proxy = self.parse_proxy_string(kwargs.pop("proxy", ""))

            super().__init__(host, port, *args, **kwargs)

        def _create_socket(self, timeout):  # used in POP3 and IMAP
            return self._get_socket(self.host, self.port, timeout)

        def _get_socket(self, host, port, timeout):  # used in SMTP
            if timeout is not None and not timeout:
                raise ValueError(
                    'Non-blocking socket (timeout=0) is not supported'
                )

            self.on_before_connection(self, host, port)

            if not self.proxy:
                sock = socket.create_connection(
                    (host, port),
                    timeout,
                    getattr(self, "source_address", None)
                )
            else:
                sock = create_connection(  # socks.create_connection
                    (host, port),
                    timeout,
                    getattr(self, "source_address", None),
                    self.proxy.proxy_type,
                    self.proxy.host,
                    self.proxy.port,
                    self.proxy.rdns,
                    self.proxy.username,
                    self.proxy.password
                )

            ssl_context = getattr(
                self, "context", None
            ) or getattr(
                self, "ssl_context", None
            )
            if ssl_context:
                return ssl_context.wrap_socket(sock, server_hostname=host)
            else:
                return sock

    return Proxified
