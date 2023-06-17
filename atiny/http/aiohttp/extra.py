try:
    from log import logger, log_stack
except ImportError:
    from atiny.log import logger, log_stack

try:
    import aiohttp
except ImportError:
    logger.info(f'need to install aiohttp for MockSave')


class MockSave:

    def __init__(self):
        self._old_is_ssl = aiohttp.ClientRequest.is_ssl
        self._old_resolver_mock = aiohttp.TCPConnector._resolve_host
        self._old_init = aiohttp.ClientRequest.__init__

    def save(self):
        self._old_is_ssl = aiohttp.ClientRequest.is_ssl
        self._old_resolver_mock = aiohttp.TCPConnector._resolve_host
        self._old_init = aiohttp.ClientRequest.__init__

    def load(self):
        aiohttp.ClientRequest.is_ssl = self._old_is_ssl
        aiohttp.TCPConnector._resolve_host = self._old_resolver_mock
        aiohttp.ClientRequest.__init__ = self._old_init
