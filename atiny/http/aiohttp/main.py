import ssl


try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback

try:
    import aiohttp
except ImportError:
    logger.info(f'need install aiohttp for MyHTTP')

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    logger.info(f'need install aiohttp_socks for socks5 ProxyConnector')

from ..proxy import Proxy
from ..cache import MyHTTPCache
from ..merge import MergeResp
from ..utils import MyHttpUtils

from .simulate import MyHttpSimulate


class MyHttp(
    MyHttpSimulate
):

    def __init__(
            self,
            timeout=(32, 16, 16),
            proxy=None, ssl_cert=None,
            version=aiohttp.HttpVersion11,
            save_cache=False, load_cache=False, save_headers=None,
            log=True,
            simulate=False, simulate_code=200, simulate_response='simulate', simulate_content_type='text/html'
    ):

        self.headers = {}
        self.proxy = Proxy(proxy)

        self.ssl_context = None
        self.ssl_cert = ssl_cert
        self._proxy_detect()

        self.timeout = aiohttp.ClientTimeout(
            *timeout,
        )
        self.version = version
        self.cache = save_cache or load_cache
        self.save_cache = save_cache
        self.save_headers = save_headers if save_headers is not None else save_cache
        self.load_cache = load_cache
        self.cache_class = MyHTTPCache(save_cache, load_cache, self.save_headers)
        self.simulate = simulate
        self.simulate_code = simulate_code
        self.simulate_response = simulate_response
        self.simulate_content_type = simulate_content_type
        self.log = log

    def _proxy_detect(self):

        if self.proxy.aio_str:
            if self.ssl_cert:
                self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                self.ssl_context.load_cert_chain(self.ssl_cert)

            #self._connector = ProxyConnector(remote_resolve=True, ssl_context=self.ssl_context)
            logger.info(f'prx: {self.proxy.aio_str}, ssl: {self.ssl_context}')
            self._connector = ProxyConnector(
                proxy_type=self.proxy.aio_type,
                host=self.proxy.adr,
                port=self.proxy.port,
                username=self.proxy.login,
                password=self.proxy.password,
                rdns=True,
                ssl=self.ssl_context,
            )
            self._connector = aiohttp.TCPConnector()
            #    'socks5://user:password@127.0.0.1:1080'
            #)

            ### or use ProxyConnector constructor
            # connector = ProxyConnector(
            #     proxy_type=ProxyType.SOCKS5,
            #     host='127.0.0.1',
            #     port=1080,
            #     username='user',
            #     password='password',
            #     rdns=True
            # )
            #self._client = ProxyClientRequest
            self._client = aiohttp.ClientRequest
        else:
            self._connector = aiohttp.TCPConnector()
            self._client = aiohttp.ClientRequest

    async def get(self, url, *args, **kwargs):
        return await self.do('get', url, *args, **kwargs)

    async def post(self, url, *args, **kwargs):
        return await self.do('post', url, *args, **kwargs)

    async def head(self, url, *args, **kwargs):
        return await self.do('head', url, *args, **kwargs)

    async def do(self, method, url, headers=None, data=None, path=None, tmp_dir='.tmp'):

        _cache_resp = self.cache_class.load_content(url=url, path=path, tmp_dir=tmp_dir)
        if _cache_resp:
            logger.info(f'loading {url} from cache')
            return _cache_resp

        if self.simulate:
            return await self._get_aresponse(
                url,
                code=self.simulate_code,
                response=self.simulate_response,
                content_type=self.simulate_content_type
            )

        cmd = getattr(self, '_'+method.lower())
        error, resp, content = await cmd(url, headers=headers, data=data)

        if error:
            return MergeResp(
                text='', content=b'', headers={},
                status=0, url=url, proxy=self.proxy,
                path=f'{tmp_dir}/'
                     f'{path}' if path and isinstance(
                    path, str
                ) else MyHttpUtils().make_path(
                    url, tmp_dir=tmp_dir,
                ),
                request_headers=headers, error=True, log=content)
        else:

            merge_resp = MergeResp(
                text=resp.text, content=content, headers=resp.headers,
                status=resp.status, url=url, proxy=self.proxy,
                path=f'{tmp_dir}/'
                     f'{path}' if path and isinstance(
                    path, str
                ) else MyHttpUtils().make_path(
                    url, tmp_dir=tmp_dir,
                ),
                request_headers=headers, error=False)

            try:
                self.cache_class.save_after_resp(merge_resp=merge_resp, update_cookies=True)
            except Exception as _tr:
                log_stack.info(f'http.{method}.path')

            return merge_resp

    async def _post(self, url, data=None, headers=None, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.post(
                        url, data=data, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth, headers=headers,
                ) as _resp:

                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info(f'http._post: {url}')
            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')

    async def _get(self, url, headers=None, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.get(
                        url, proxy=self.proxy.aio_str, proxy_auth=self.proxy.aio_auth,
                        headers=headers,
                ) as _resp:

                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info(f'http._get: {url}')
            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')

    async def _head(self, url, headers=None, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.head(
                        url, proxy=self.proxy.aio_str, proxy_auth=self.proxy.aio_auth,
                        headers=headers) as _resp:

                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info(f'http._head: {url}')
            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')
