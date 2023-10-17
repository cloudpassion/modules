import os
import pathlib
import urllib.parse


try:
    from log import logger
except ImportError:
    from ..log import logger

try:
    import dns.resolver
except ImportError:
    logger.info(f'need install dnspython for dns.resolver')


CONSOLE_SERVICES = {
    'ip': 'http://l2.io/ip'
}


class MyHttpUtils:

    def get_ua(self):
        return 'Mozilla/5.0 (X11; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'

    def make_path(
            self, url, tmp_dir='.', version=1, data=''
    ):
        if version == 2:

            method = url.split(' ')[0]
            url = url.replace(f'{method} ', '')
            # scheme = url.split(':')[0]
            host = url.split('/')[2]
            # path = url.split('/')[3]

            if url:
                ret = url.replace(':', '.').replace('?', '.').replace('/', '.').replace('&', '.')[0:200]
            else:
                ret = None

            if data:
                data = data.replace(':', '.').replace('?', '.').replace('/', '.').replace(
                    '&', '.'
                ).replace(']', '').replace('[', '').replace('{', '').replace('}', '')
                ret = f'{ret}{data}'

            return f'{tmp_dir}/{host}/{method}/{ret}'[0:200] if tmp_dir and isinstance(
                tmp_dir, str
            ) and isinstance(ret, str) else ret

        if url:
            ret = url.replace(':', '.').replace('?', '.').replace('/', '.').replace('&', '.')[0:200]
        else:
            ret = None

        return f'{tmp_dir}/{ret}' if tmp_dir and isinstance(
            tmp_dir, str
        ) and isinstance(ret, str) else ret

    def make_dirs(self, path):
        pathlib.Path(
            os.path.dirname(
                os.path.abspath(path)
            )
        ).mkdir(parents=True, exist_ok=True)

    # REWRITE DEFAULT REQUEST RESOLVER FOR DNS WITHOUT /etc/hosts ############################
    def dns_resolver(self, host, dnssrv):
        r = dns.resolver.Resolver()
        r.nameservers = [dnssrv]
        answer = r.query(host)
        for rdata in answer:
            return str(rdata)

    def quote(self, text, colon=False, *args, **kwargs):
        if not colon:
            return urllib.parse.quote(text, *args, **kwargs)

        _quoted = urllib.parse.quote(text, *args, **kwargs)
        return _quoted.replace(':', '%3A')

    def quote_plus(self, text, *args, **kwargs):
        return urllib.parse.quote_plus(text, *args, **kwargs)

    def urlencode(self, text):
        return urllib.parse.urlencode(text, quote_via=self.quote)
