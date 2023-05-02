
try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback

try:
    import requests
    import requests.structures
    import requests.cookies
except ImportError:
    logger.info(f'need install requests for MyRequestsHTTP')

try:
    import urllib3
except ImportError:
    logger.info(f'need install urllib3')

from collections import defaultdict

from ..proxy import Proxy
from ..cache import MyHTTPCache
from ..merge import MergeResp
from ..utils import MyHttpUtils
from ..simulate import requests_simulate

from .rewrites import MyRequestsRewrites


class MyRequestsHTTP(
    MyRequestsRewrites
):

    def __init__(
            self,
            proxy=None, headers=None,
            save_cache=False, load_cache=False, save_headers=None,
            simulate=False, simulate_code=200, simulate_resp='simulate',
            simulate_content_type='text/html',
            ssl_cert=False,
            log=False,
            # connection, conn and retrieve, tries
            timeout=(10, 20, 3),
            # address of dns server
            dns_rewrite_address=None,
    ):

        self.session = requests.Session()

        self.proxy = Proxy(proxy)
        if self.proxy.str:
            logger.info(f'set proxy: {self.proxy.str}')
            self.session.proxies = \
                dict(http=self.proxy.str,
                     https=self.proxy.str)

        if ssl_cert:
            logger.info(f'set cert: {ssl_cert}')
            self.session.verify = ssl_cert

        self.ssl_cert = ssl_cert
        # cache
        self.cache = save_cache or load_cache
        self.save_cache = save_cache
        self.load_cache = load_cache
        self.save_headers = save_headers if save_headers is not None else save_cache
        self.cache_class = MyHTTPCache(save_cache, load_cache, self.save_headers)

        # simulate response
        self.simulate = simulate
        self.simulate_code = simulate_code
        self.simulate_resp = simulate_resp
        self.simulate_content_type = simulate_content_type

        self.rewrite_retries(
            timeout[2],
        )
        self.timeout = timeout[:2]

        self.log = log

        req_headers = {
            'def': requests.structures.CaseInsensitiveDict(
                headers) if headers else requests.structures.CaseInsensitiveDict(self.session.headers)
        }
        self.request_headers = defaultdict(
            dict, **req_headers)

        self.rewrite_dns(
            dns_rewrite_address
        )

    def do(self, method, url, path=None, tmp_dir='.tmp', *args, **kwargs):

        url_domain = url.split('/')[2:3][0]
        new_kwargs = kwargs.copy()
        logger.info(f'url_domain: {url_domain}')
        logger.info(f'self.sess.ssl: {self.session.verify}')
        logger.info(f'kw.get: {new_kwargs.get("verfiy")}, kw: {new_kwargs}')

        #if 'headers' in kwargs:
        #    _headers = requests.structures.CaseInsensitiveDict(kwargs.get('headers'))
        #else:
        if url_domain in self.request_headers:
            _headers = self.request_headers.get(url_domain)
        else:
            _headers = self.request_headers.get('def')

        if kwargs.get('headers'):
            _headers.update(kwargs.get('headers'))

        for h_key, h_value in _headers.copy().items():
            if not h_value:
                del _headers[h_key]

        if _headers.get('Cookie'):
            self.session.cookies = requests.cookies.cookiejar_from_dict(
                {v.split('=')[0]: v.split('=')[1] for v in _headers.get('Cookie').split('; ')}
            )
        else:
            if kwargs.get('clear_cookie'):
                self.session.cookies.clear()

        #self.session.headers = _headers
        self.request_headers[url_domain] = _headers

        new_kwargs.update({'headers': _headers})

        _cache_resp = self.cache_class.load_content(url=url, path=path, tmp_dir=tmp_dir)
        if _cache_resp:
            logger.info(f'loading {url} from cache')
            return _cache_resp

        if self.simulate:
            try:
                return requests_simulate(
                    url, code=self.simulate_code, response=self.simulate_resp,
                    content_type=self.simulate_content_type
                )
            except Exception:
                log_stack.error(f'in simulate')

        command = getattr(self, '_'+method)
        error, resp = command(url, *args, **new_kwargs)

        if error:
            return MergeResp(
                text='', content=b'', headers={}, status=0, url=url, error=True, log=resp,
                path=f'{tmp_dir}/'
                     f'{path}' if path and isinstance(
                    path, str
            ) else MyHttpUtils().make_path(
                    url, tmp_dir=tmp_dir,
                ),
                proxy=self.proxy, request_headers=dict(self.request_headers[url_domain]))

        merge_resp = MergeResp(
            text=resp.text, content=resp.content, headers=resp.headers,
            status=resp.status_code, url=url, proxy=self.proxy,
            path=f'{tmp_dir}/'
                 f'{path}' if path and isinstance(
                path, str
            ) else MyHttpUtils().make_path(
                url, tmp_dir=tmp_dir,
            ),
            request_headers=dict(self.request_headers[url_domain]),
            error=False
        )

        self.cache_class.save_after_resp(merge_resp=merge_resp, update_cookies=True)

        #self.request_headers[url_domain] = \
        #    self.cache_class.save_after_resp(url, save_resp=self.cache,
        #                                     headers=self.request_headers[url_domain],
        #                                     resp=merge_resp, error=False, tmp_dir='.tmp/')
        new_cookie = resp.headers.get('Set-Cookie')
        self.session.cookies = new_cookie

        #self.session.headers = self.request_headers[url_domain]

        return merge_resp

    def get(self, url, *args, **kwargs):
        return self.do('get', url
                       , *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.do('post', url, *args, **kwargs)

    def head(self, url, *args, **kwargs):
        return self.do('head', url,
                       *args, **kwargs)

    def _get(self, url, *args, **kwargs):
        try:
            return False, self.session.get(url, **kwargs)
            #return False, requests.get(url, *args, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info('http.post')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.get.Exception: ')

    def _post(self, url, *args, **kwargs):
        try:
            return False, self.session.post(url, *args, **kwargs)
            #return False, requests.post(url, *args, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info('http.post')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.post.Exception: ')

    def _head(self, url, *args, **kwargs):
        try:
            return False, self.session.head(url, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info('http.head')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.head.Exception: ')

