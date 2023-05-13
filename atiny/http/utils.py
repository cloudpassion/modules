import os
import pathlib


try:
    from log import logger
except:
    from atiny.log import logger

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

    def make_path(self, url, tmp_dir='.'):
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
