import re

try:
    from log import logger, log_stack
except ImportError:
    from ...log import logger, log_stack

try:
    import requests
    import requests.adapters
except ImportError:
    logger.info(f'need install requests for MyRequestsHTTP')

try:
    import urllib3
except ImportError:
    logger.info(f'need install urllib3')

try:
    import dns.resolver
except ImportError:
    logger.info(f'need install dnspython for dns.resolver')


from ..utils import MyHttpUtils

from .default import MyRequestsDefault


class MyRequestsRewrites(
    MyRequestsDefault
):

    def rewrite_dns(self, dns_rewrite_address):
        if not dns_rewrite_address:
            return

        if not isinstance(dns_rewrite_address, str):
            dns_rewrite_address = '1.1.1.1'

        self.rewrite_dns_address = dns_rewrite_address
        self._orig_create_connection = connection.create_connection
        connection.create_connection = self._patched_create_connection

    def _patched_create_connection(self, address, *args, **kwargs):
        #""Wrap urllib3's create_connection to resolve the name elsewhere"""
        # resolve hostname to an ip address; use your own
        # resolver here, as otherwise the system resolver will be used.
        host, port = address
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host.lower()):
            hostname = host
        else:
            hostname = MyHttpUtils().dns_resolver(host, self.rewrite_dns_address)

        return self._orig_create_connection((hostname, port), *args, **kwargs)

    def rewrite_retries(self, connection_tries):

        try:
            max_tries = urllib3.util.retry.Retry(connect=connection_tries, backoff_factor=0.5)
            adapter = requests.adapters.HTTPAdapter(max_retries=max_tries)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        except Exception:
            log_stack.error(f'rewrite_retries')
