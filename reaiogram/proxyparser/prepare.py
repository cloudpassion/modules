try:
    # TODO: fix selenium import
    from selenium.webdriver.common.proxy import Proxy
    SELENIUM = True
except ImportError:
    SELENIUM = False


class AbstractProxy:

    proxy = None
    dns_proxy = None
    scheme = None
    ip = None
    port = None
    login = None
    password = None
    ssl_certs = None
    selenium = None
    selenium_raw = dict()


class PrepareProxy(AbstractProxy):

    def prepare(self):
        if not self.proxy:
            return

        for tp in ['SELENIUM', ]:
            f = getattr(self, f'prepare_{tp.lower()}')
            f()

    def prepare_selenium(self):
        if 'socks' in self.scheme:
            raw = ({
                'socksProxy': '192.168.66.232:53140',
                'socksUsername': self.login,
                'socksPassword': self.password
            })

        else:
            raw = {
                'autodetect': True,
                '1': self.proxy
            }

        self.selenium = Proxy(raw)
        self.selenium_raw = raw
        #print(f'{self.selenium=}')
        '''
        if raw is not None:
            if 'proxyType' in raw and raw['proxyType'] is not None:
                self.proxy_type = ProxyType.load(raw['proxyType'])
            if 'ftpProxy' in raw and raw['ftpProxy'] is not None:
                self.ftp_proxy = raw['ftpProxy']
            if 'httpProxy' in raw and raw['httpProxy'] is not None:
                self.http_proxy = raw['httpProxy']
            if 'noProxy' in raw and raw['noProxy'] is not None:
                self.no_proxy = raw['noProxy']
            if 'proxyAutoconfigUrl' in raw and raw['proxyAutoconfigUrl'] is not None:
                self.proxy_autoconfig_url = raw['proxyAutoconfigUrl']
            if 'sslProxy' in raw and raw['sslProxy'] is not None:
                self.sslProxy = raw['sslProxy']
            if 'autodetect' in raw and raw['autodetect'] is not None:
                self.auto_detect = raw['autodetect']
            if 'socksProxy' in raw and raw['socksProxy'] is not None:
                self.socks_proxy = raw['socksProxy']
            if 'socksUsername' in raw and raw['socksUsername'] is not None:
                self.socks_username = raw['socksUsername']
            if 'socksPassword' in raw and raw['socksPassword'] is not None:
                self.socks_password = raw['socksPassword']
        '''
