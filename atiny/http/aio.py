""" http communicate """

import asyncio
setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)

import logging
import pathlib
import time
import os
import re
import random
import traceback
import uuid
import urllib3
try:
    import requests.adapters
    import requests.structures
    import requests.cookies
except ImportError:
    pass

import socks

try:
    import websockets
    import aresponses
    import responses
    import dns.resolver
except ImportError:
    pass

import aiohttp
import ujson as json
import ssl
import certifi

from pathlib import Path
from collections import deque, defaultdict
from aiohttp import BasicAuth

try:
    from aiosocksy import Socks5Auth
    from aiosocksy.connector import ProxyClientRequest
    from aiohttp_socks import ProxyConnector, ProxyType
    from urllib3.util import connection
except ModuleNotFoundError:
    pass

try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ..log import logger, log_stack, parse_traceback


console_services = {'ip': 'http://l2.io/ip'}


def _load_json_from_file(file_name):

    if os.path.isfile(file_name):
        with open(file_name, 'r') as rf:
            try:
                js = json.loads(rf.read())
            except:
                js = {}
    else:
        js = {}

    return js if js else {}


def _save_json_to_file(file_name, to_write_js, update=False):

    if os.path.isfile(file_name):
        if update:
            with open(file_name, 'r') as rf:
                try:
                    old_js = json.loads(rf.read())
                except Exception:
                    old_js = {}
            if old_js:
                old_js.update(to_write_js if to_write_js else {})
                to_write_js = old_js
    else:
        pathlib.Path(os.path.dirname(os.path.abspath(file_name))).mkdir(parents=True, exist_ok=True)

    with open(file_name, 'w') as wf:
        wf.write(json.dumps(dict(to_write_js) if dict(to_write_js) else {}))

    return to_write_js if to_write_js else {}


# REWRITE DEFAULT REQUEST RESOLVER FOR DNS WITHOUT /etc/hosts ############################
def dns_resolver(host, dnssrv):
    r = dns.resolver.Resolver()
    r.nameservers = [dnssrv]
    answer = r.query(host)
    for rdata in answer:
        return str(rdata)


class MergeResp:
    def __init__(
            self, text=r'', content=b'', headers={}, status=0, url=None,
            error=True, proxy=None, path=None, request_headers={}, log='', resp=None):

        self.resp = resp
        self.text = text
        self.status = status
        self.content = content
        self.headers = headers
        self.cookies = {}
        self.url = url
        self.error = error
        self.proxy = proxy
        self.path = path
        self.request_headers = request_headers
        self.log = log


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
                    if 'socks' in self.scheme:
                        self.aio_auth = Socks5Auth(login=self.login, password=self.password)
                    else:
                        self.aio_auth = BasicAuth(login=self.login, password=self.password)



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


class MyHttpUtils:

    def get_ua(self):
        return 'Mozilla/5.0 (X11; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'

    def make_path(self, url, tmp_dir=''):
        if url:
            ret = url.replace(':', '.').replace('?', '.').replace('/', '.').replace('&', '.')[0:200]
        else:
            ret = None

        return tmp_dir+ret if tmp_dir and isinstance(tmp_dir, str) and isinstance(ret, str) \
            else ret


class MyHTTPCache:

    def __init__(self, save_cache=False, load_cache=False, log=False):
        self.save_cache = save_cache
        self.load_cache = load_cache
        self.log = log

    def save_after_resp(self, merge_resp=None, update_cookies=False):

        if not self.save_cache:
            return

        if merge_resp and not merge_resp.error:
            try:
                self.save_content(
                    save_resp=self.save_cache, save_headers=self.save_cache,
                    merge_resp=merge_resp)

                _headers = merge_resp.request_headers
                _set_cookies = '; '.join(
                    [v.split(';')[0] for k, v in merge_resp.headers.items() if k == 'Set-Cookie']
                )
                merge_resp.cookies.update({
                    v.split(';')[0].split('=')[0]: v.split(';')[0].split('=')[1] for k, v in merge_resp.headers.items() if k == 'Set-Cookie'
                })

                if update_cookies:
                    if merge_resp.headers.get(
                            'Set-Cookie') and _set_cookies != merge_resp.request_headers.get('Cookie'):
                        _headers.update({'Cookie': _set_cookies})

                self.headers_detect(
                    'save', merge_resp.path+'.request_headers',
                    save_data=_headers, update=False)

                return self.headers_detect('update', merge_resp.headers, merge_resp.request_headers)
            except Exception:
                log_stack.error('MyHTTPCache.save_after_resp')

    def headers_detect(self, operation, headers_data={}, save_data={}, update=True):

        if operation == 'save':
            _save_json_to_file(headers_data, save_data, update=update)
            return save_data

        elif operation == 'load':
            _headers = _load_json_from_file(headers_data)
            if _headers.get('Cookie'):
                _cookies = {'Cookie': _headers.get('Cookie')}
                _headers.update(_cookies)
            return _headers

        elif operation == 'update':
            _heads = save_data.copy()
            _server_headers = headers_data.copy()
            _set_cookies = '; '.join(
                [v.split(';')[0] for k, v in _server_headers.items() if k == 'Set-Cookie']
            )
            if not _set_cookies:
                _set_cookies = {}

            if 'Set-Cookie' in _server_headers and _set_cookies != save_data.get('Cookie'):
                _heads.update({'Cookie': _set_cookies})
                return _heads

            return _heads

    def load_content(self, path='.test.http.html', url=None, tmp_dir=''):

        if not self.load_cache:
            return None

        if path and isinstance(path, str):
            path = tmp_dir+path
        else:
            path = MyHttpUtils().make_path(url, tmp_dir=tmp_dir)

        if not os.path.isfile(path):
            if self.log:
                logger.info(f'load_content not path: {path}')
            return None
        else:
            _json = _load_json_from_file(path + '.status_code')
            _status = _json.get('status') if _json else 0
            _headers = self.headers_detect(
                'load', headers_data=path+'.server_headers')

            with open(path, 'rb') as crb:
                _content = crb.read()

            return MergeResp(
                text='', content=_content, headers=_headers, status=_status,
                path=path, url=url, error=False,
            )

    def save_content(self,
                     save_resp=False, save_headers=False, merge_resp=None):

        if not self.save_cache:
            return None

        if merge_resp and not merge_resp.error:

            if save_resp:
                if self.log:
                    logger.info(f'spath: {merge_resp.path}')
                pathlib.Path(
                    os.path.dirname(
                        os.path.abspath(merge_resp.path))).mkdir(parents=True, exist_ok=True)

                if self.log:
                    logger.info(f'save_content: {merge_resp.path}')
                with open(merge_resp.path, 'wb') as fw:
                    fw.write(merge_resp.content)

            """ try save server_headers if request failed with not 200 http.code """
            if save_headers:
                pathlib.Path(
                    os.path.dirname(
                        os.path.abspath(merge_resp.path))).mkdir(parents=True, exist_ok=True)
                with open(merge_resp.path + '.server_headers', 'w') as sw, \
                        open(merge_resp.path + '.status_code', 'w') as cw:
                    try:
                        sw.write(json.dumps({k: v for k, v in merge_resp.headers.items()}))
                        cw.write(json.dumps({'status': merge_resp.status}))
                    except Exception as _tr:
                        log_stack.error('save_content')


class MyRequestsHTTP:

    def __init__(self, con_try=3, proxy=None,
                 headers=requests.structures.CaseInsensitiveDict({}),
                 save_cache=False, load_cache=False, simulate=False, log=True,
                 cache_code=200, cache_text='simulate', cache_json={},
                 cache_content_type='text/html',
                 ssl_cert=False,
                 timeout=(10, 20), max_redirects=1, dns_rewrite=False,
                 dns_rewrite_address='8.8.8.8',
                 cache_class=None,
                 *args, **kwargs
                 ):

        self.session = requests.Session()

        self.proxy = Proxy(proxy)
        if self.proxy.str:
            #logger.info(f'set proxy: {self.proxy.str}')
            self.session.proxies = \
                dict(http=self.proxy.str,
                     https=self.proxy.str)

        if ssl_cert:
            logger.info(f'set cert: {ssl_cert}')
            self.session.verify = ssl_cert

        self.ssl_cert = ssl_cert
        self.cache = save_cache or load_cache
        self.save_cache = save_cache
        self.load_cache = load_cache
        self.cache_class = cache_class or MyHTTPCache(save_cache, load_cache)
        self.simulate = simulate
        self.code = cache_code
        self.cache_text = cache_text
        self.cache_json = cache_json
        self.cache_content_type = cache_content_type

        retry = urllib3.util.retry.Retry(connect=con_try, backoff_factor=0.5)
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.max_redirects = max_redirects
        self.timeout = timeout
        self.log = log

        req_headers = {
            'def': requests.structures.CaseInsensitiveDict(
                headers) if headers else requests.structures.CaseInsensitiveDict(self.session.headers)
        }
        self.request_headers = defaultdict(
            dict, **req_headers)

        if dns_rewrite:
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
            hostname = dns_resolver(host, self.rewrite_dns_address)

        return self._orig_create_connection((hostname, port), *args, **kwargs)

    def do(self, method, url, path=None, tmp_dir='.tmp', *args, **kwargs):

        url_domain = url.split('/')[2:3][0]
        new_kwargs = kwargs.copy()
        # logger.info(f'url_domain: {url_domain}')
        #logger.info(f'self.sess.ssl: {self.session.verify}')
        #logger.info(f'kw.get: {new_kwargs.get("verfiy")}, kw: {new_kwargs}')

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
            try:
                self.session.cookies = requests.cookies.cookiejar_from_dict(
                    {v.split('=')[0]: v.split('=')[1] for v in _headers.get('Cookie').split('; ')}
                )
            except:
                pass
        else:
            if kwargs.get('clear_cookie'):
                self.session.cookies.clear()

        #logger.info(f'z1')
        #self.session.headers = _headers
        self.request_headers[url_domain] = _headers

        new_kwargs.update({'headers': _headers})

        _cache_resp = self.cache_class.load_content(
            url=url, path=path, tmp_dir=tmp_dir
        )
        if _cache_resp:
            logger.info(f'loading {url} from cache')
            return _cache_resp

        #logger.info(f'z2')
        if self.simulate:
            return requests_simulate(
                url, text=self.cache_text, js=self.cache_json,
                content_type=self.cache_content_type)

        # logger.info(f'z3')
        command = getattr(self, '_'+method)
        error, resp = command(url, *args, **new_kwargs)
        # logger.info(f'z4')

        if error:
            logger.info(f'error')
            return MergeResp(
                text='', content=b'', headers={}, status=0, url=url, error=True, log=resp,
                path=tmp_dir+path if path \
                                and isinstance(path, str) \
                                else MyHttpUtils().make_path(url, tmp_dir=tmp_dir) \
                                if self.cache or path else None,
                proxy=self.proxy,
                request_headers=dict(self.request_headers[url_domain]))

        merge_resp = MergeResp(
            text=resp.text, content=resp.content, headers=resp.headers,
            status=resp.status_code, url=url, proxy=self.proxy,
            path=tmp_dir+path if path \
                                 and isinstance(path, str) \
                                 else MyHttpUtils().make_path(url, tmp_dir=tmp_dir) \
                                 if self.cache or path else None,
            request_headers=dict(self.request_headers[url_domain]),
            error=False
        )

        #logger.info(f'z5')
        self.cache_class.save_after_resp(merge_resp=merge_resp, update_cookies=True)
        #logger.info(f'z6')

        #self.request_headers[url_domain] = \
        #    self.cache_class.save_after_resp(url, save_resp=self.cache,
        #                                     headers=self.request_headers[url_domain],
        #                                     resp=merge_resp, error=False, tmp_dir='.tmp/')
        new_cookie = resp.headers.get('Set-Cookie')
        #logger.info(f'set-cookie: {new_cookie}')
        #logger.info(f'resp.h: {resp.headers}')

        #self.session.headers = self.request_headers[url_domain]

        return merge_resp

    def get(self, url, *args, **kwargs):
        return self.do('get', url
                       , *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.do('post', url, *args, **kwargs)

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
                log_stack.error('http.get')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.get.Exception: ')

    def _post(self, url, *args, **kwargs):
        try:
            return False, self.session.post(url, *args, **kwargs)
            #return False, requests.post(url, *args, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error('http.post')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.get.Exception: ')

    def _put(self, url, *args, **kwargs):
        try:
            return False, self.session.put(url, *args, **kwargs)
            #return False, requests.post(url, *args, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error('http.put')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.get.Exception: ')

    def _head(self, url, *args, **kwargs):
        try:
            return False, self.session.head(url, **kwargs)
        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error('http.head')
            return True, parse_traceback(_tr, 'MyRequestsHTTP.get.Exception: ')


class MyHttp:

    def __init__(self, timeout=aiohttp.ClientTimeout(total=64, sock_connect=32, sock_read=32),
                 proxy=None, ssl_cert=None, version=aiohttp.HttpVersion11,
                 save_cache=False, load_cache=False, simulate=False, log=True,
                 cache_code=200, cache_text='simulate', cache_content_type='text/html',
                 cache_class=None,
                 ):

        self.headers = {}
        self.proxy = Proxy(proxy)

        self.ssl_context = None
        self.ssl_cert = ssl_cert
        self._proxy_detect()

        self.timeout = timeout
        self.version = version
        self.cache = save_cache or load_cache
        self.save_cache = save_cache
        self.load_cache = load_cache
        self.cache_class = cache_class or MyHTTPCache(save_cache, load_cache, log)
        self.simulate = simulate
        self.code = cache_code
        self.cache_text = cache_text
        self.cache_content_type = cache_content_type
        self.log = log

    def _proxy_detect(self):

        if self.proxy.aio_str:
            if self.ssl_cert:
                #logger.info(f'load ssl_context')
                self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                self.ssl_context.load_cert_chain(self.ssl_cert)

            #self._connector = ProxyConnector(remote_resolve=True, ssl_context=self.ssl_context)
            #logger.info(f'prx: {self.proxy.aio_str}, ssl: {self.ssl_context}')
            # self._connector = ProxyConnector(
            #     proxy_type=ProxyType.HTTP,
            #     #self.proxy.aio_type,
            #     host=self.proxy.adr,
            #     port=self.proxy.port,
            #     username=self.proxy.login,
            #     password=self.proxy.password,
            #     rdns=True,
            #     ssl=self.ssl_context,
            # )
            self._connector = aiohttp.TCPConnector()
            self._connector = aiohttp.TCPConnector(
                ssl_context=self.ssl_context,
                use_dns_cache=False,
            )
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

    async def delete(self, url, *args, **kwargs):
        return await self.do('delete', url, *args, **kwargs)

    async def get(self, url, *args, **kwargs):
        return await self.do('get', url, *args, **kwargs)

    async def post(self, url, *args, **kwargs):
        return await self.do('post', url, *args, **kwargs)

    async def head(self, url, *args, **kwargs):
        return await self.do('head', url, *args, **kwargs)

    async def options(self, url, *args, **kwargs):
        return await self.do('head', url, *args, **kwargs)

    async def patch(self, url, *args, **kwargs):
        return await self.do('patch', url, *args, **kwargs)

    async def do(self, method, url, headers={}, data=None, path=None, tmp_dir='.tmp/',
                 *args, **kwargs):

        _cache_resp = self.cache_class.load_content(url=url, path=path, tmp_dir=tmp_dir)
        if _cache_resp:
            if self.log:
                logger.info(f'loading {url} from cache')
            return _cache_resp

        if self.simulate:
            return await self.get_aresponse(
                url, text=self.cache_text, content_type=self.cache_content_type)

        cmd = getattr(self, '_'+method.lower())
        error, resp, content = await cmd(url, headers=headers, data=data, *args, **kwargs)

        if error:
            return MergeResp(
                text='', content=b'', headers={},
                status=0, url=url, proxy=self.proxy,
                path=tmp_dir+path if path \
                                    and isinstance(path, str) \
                                    else MyHttpUtils().make_path(url, tmp_dir=tmp_dir) \
                                    if self.cache or path else None,
                request_headers=headers, error=True, log=content)
        else:

            merge_resp = MergeResp(
                text=resp.text, content=content, headers=resp.headers,
                status=resp.status, url=url, proxy=self.proxy,
                path=tmp_dir+path if path and isinstance(
                    path, str
                ) else MyHttpUtils().make_path(
                    url, tmp_dir=tmp_dir
                )
                if self.cache or path else None,
                resp=resp,
                request_headers=headers, error=False)

            try:
                self.cache_class.save_after_resp(merge_resp=merge_resp, update_cookies=True)
            except Exception as _tr:
                if kwargs.get('log') or self.log:
                    log_stack.info(f'http.{method}.path')

            return merge_resp

    async def _delete(self, url, data=None, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client,
            ) as session:
                async with session.delete(
                        url, data=data, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth, headers=headers,
                        ssl=self.ssl_context, **kwargs
                ) as _resp:

                    _content = await _resp.read()
                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._delete: {url}')

            return True, b'', parse_traceback(_tr, 'http.delete.Exception: ')

    async def _post(self, url, data=None, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client,
            ) as session:
                async with session.post(
                        url, data=data, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth, headers=headers,
                        ssl=self.ssl_context, **kwargs
                ) as _resp:

                    _content = await _resp.read()
                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._post: {url}')

            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')

    async def _get(self, url, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.get(
                        url, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth,
                        ssl=self.ssl_context,
                        headers=headers, **kwargs
                ) as _resp:

                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._get: {url}')
            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')

    async def _s_get(self, url, headers={}, status=None, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.get(
                        url, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth,
                        ssl=self.ssl_context,
                        headers=headers, **kwargs
                ) as _resp:

                    if status and _resp.status == status:
                        _content = await _resp.read()
                    else:
                        _content = None

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._get: {url}')
            return True, None, None

    async def _options(self, url, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.options(
                        url, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth,
                        ssl=self.ssl_context,
                        headers=headers, **kwargs
                ) as _resp:

                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._options: {url}')
            return True, b'', parse_traceback(_tr, 'http.options.Exception: ')

    async def _head(self, url, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client) as session:
                async with session.head(
                        url, proxy=self.proxy.aio_str, proxy_auth=self.proxy.aio_auth,
                        headers=headers,
                        ssl=self.ssl_context, **kwargs
                ) as _resp:

                    # if 'allow_redirects' in kwargs and not kwargs.get('allow_redirects'):
                    #     _content = _resp
                    # else:
                    _content = await _resp.read()

                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.info(f'http._head: {url}')
            return True, b'', parse_traceback(_tr, 'http.post.Exception: ')

    async def _patch(self, url, headers={}, **kwargs):

        try:
            async with aiohttp.ClientSession(
                    connector=self._connector, timeout=self.timeout,
                    version=self.version, request_class=self._client,
            ) as session:
                async with session.patch(
                        url, proxy=self.proxy.aio_str,
                        proxy_auth=self.proxy.aio_auth, headers=headers,
                        ssl=self.ssl_context, **kwargs
                ) as _resp:

                    _content = await _resp.read()
                    return False, _resp, _content

        except Exception as _tr:
            if kwargs.get('log') or self.log:
                log_stack.error(f'http._patch: {url}')

            return True, b'', parse_traceback(_tr, 'http.patch.Exception: ')

    async def get_urls_semaphore(self, tasks_timeouts, command, log=False):

        async with self.sem:
            if tasks_timeouts:
                _sleep = random.randint(tasks_timeouts[0], tasks_timeouts[1])
                await asyncio.sleep(_sleep)

            task_result = await command
            if log:
                logger.info(f'end')
                
            return task_result

    async def get_urls(
            self, links, max_tasks=100, tasks_timeouts=None,
            ssl_cert=None, sem_log=False,
            save_resp=False, save_headers=False, tmp_dir='.tmp/',
    ):

        #logger.info(links)
        _headers_file = None
        tasks = []
        self.sem = asyncio.Semaphore(max_tasks)

        for link in links:
            _headers = {}
            _path = None
            if isinstance(link, list) or isinstance(link, tuple):
                _url = link[0]
                try:
                    _path = link[1]
                except IndexError: pass

                if len(link) >= 3:
                    if isinstance(link[2], str):
                        _headers_file = link[2]
                    elif isinstance(link[2], dict):
                        _headers = link[2]
                    else:
                        pass

                if len(link) >= 4:
                    _save_override = link[3]
                else:
                    _save_override = False
            else:
                _url = link
                _save_override = False
                _headers_file = None

            if not _path:
                #_path = _url.split('/')[2:3][0]
                _path = '.'.join(_url.split('/')[3:])

            #logger.info(f'get_urls:url: {_url}, path: {tmp_dir + _path}')

            if not _headers_file:
                _headers_file = _path+'.request_headers'
            if not _headers:
                _headers = self.cache_class.headers_detect(
                    'load', headers_data=_headers_file)
            #tasks.append(
            #    asyncio.create_task(
            #        MyHttp(proxy=self.proxy).get(
            #            url=_url, path=_path, headers=_headers, tmp_dir=tmp_dir)
            #    )
            #)
            tasks.append(
                asyncio.create_task(self.get_urls_semaphore(
                    tasks_timeouts,
                    MyHttp(
                        log=self.log, proxy=self.proxy, 
                        ssl_cert=ssl_cert, version=self.version,
                        timeout=self.timeout,
                    ).do(
                        'get',
                        url=_url, path=_path, headers=_headers, tmp_dir=tmp_dir),
                    log=sem_log,
                )
                )
            )

        results = await asyncio.gather(*tasks)

        for result in results:
            if not result:
                continue
            if not result.error:
                if result.status != 200 and result.status != 206:
                    try:
                        logger.info(f'url: |{result.url}| content: {result.content[:100]}\n\n'
                                    f's_headers: {result.headers}\n\n'
                                    f'status: {result.status}\n\n')
                    except:
                        logger.info(f'url: |{result.url}:{result.status}')
                self.cache_class.save_after_resp(
                    merge_resp=result, update_cookies=True
                )

            else:
                logger.info(f'bad result: {result}')

        return results

    async def get_aresponse(self, url='http://ggg', code=200,
                            text='simulate', content_type='text/html'):
        event_loop = asyncio.get_event_loop()
        async with aresponses.ResponsesMockServer(loop=event_loop) as arsps:
            arsps.add(''.join(url.split('/')[2:]), '/', 'get',
                      arsps.Response(
                          body=text,
                          headers={"Content-Type": content_type}
                      )
                      )

            async with aiohttp.ClientSession(loop=event_loop) as session:

                async with session.get(url) as response:
                    text = await response.text()
                    _content = await response.read()

        return False, _content, MergeResp(
            text=text, headers=response.headers, status=code
        )


class MyUrls:

    where = ('reddit', 'imgur.com', )

    def __init__(self, data=None, where=False, what=None, proxy=None):
        self.data = data
        self.url = None
        self.links = None
        self.what = what
        self.where = where
        self.recompile = \
            ('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', )
        self.skip_urls = set()
        self.aio_http = False
        self.req_http = False

        if self.what:
            self.aio_http = MyHttp(proxy=proxy)
            self.req_http = MyRequestsHTTP(proxy=proxy)

        #self.conf = MyConfig()
        #self.conf.init(f'{"/".join(str(Path(__file__)).split("/")[:-1])}/.def.ni')

    async def check(self):
        if not self.where:
            return await self.find_urls()
        else:
            if self.where == 'reddit':
                self.recompile = (r'<span><a href="(.*?)">\[link\]</a>',
                                   'src="(.*?)(?: |")')
            else: pass

    async def tiny(self, _url):
        await asyncio.sleep(0)
        return _url

    def get_domain(self, url):
        return url.split('/')[2::1]

    async def check_domain(self, _url):

        if not self.what:
            return [True, _url]

        elif self.what == 'media':

            if not _url:
                return [False, _url]

            url_domain = _url.split('/')[2:3]
            if not url_domain:
                logger.debug(f'domain check: {_url}')
                return [False, False]

            if _url.split('?')[0] in self.skip_urls:
                return [False, False]

            self.skip_urls.add(_url.split('?')[0])

            try:
                if 'imgur.com' in url_domain[0] and not 'i.imgur.com' in url_domain[0]:
                    if 'jpg' in _url or 'png' in _url or 'jpeg' in _url or 'bmp' in _url:
                        return [True, _url]
                    return [False, _url, '<link rel="image_src".*?href="(.*?)"']

                elif re.search('deviantart.com', url_domain[0]):
                    return [False, _url, 'data-super-full-img="(.*?)"']

                elif re.search('flickr.com', url_domain[0]):
                    return [False, _url, '<meta property="og:image" content="(.*?)"']

                elif re.search('www.reddit.com', url_domain[0]):
                    #return get_img(re.findall(
                    # '<meta name="description" content="(htt[p|ps]:.*?[\.jpg|\.png|\.jpeg|\.bmp]) ', r.text))[0]
                    logger.debug(f'check_wwwredditcom: {_url}')
                    return [False, False]

                elif re.search('asciinema.org', url_domain[0]):
                    return [False, _url, r'<meta property="og:image" content="(.*?)"']

                elif re.search('upload.wikimedia.org', url_domain[0]):
                    try:
                        _wiki = _url+'/1024px-'+_url.split('/')[-1]
                    except:
                        _wiki = _url
                        log_stack.info(f'FIX_WIKI_IMG: {_url}')
                    return [True, _wiki]

                elif re.search('youtube.com', url_domain[0]) or re.search('youtu.be', url_domain[0]) or re.search('www.youtube.com', url_domain[0]) or re.search('www.youtu.be', url_domain[0]):
                    try: _ytb_t = _url.split('v%3D')[1].split('%')[0]
                    except:
                        try: _ytb_t = _url.split('v=')[1].split('&')[0]
                        except:
                            try: _ytb_t = _url.split('v=')[1]
                            except:
                                try: _ytb_t = _url.split('/')[-1]
                                except:
                                    log_stack.info(f'FIXYTB_RETURN_FALSE: {_url}')
                                    return [False, False]

                    try: _ytb_t = _ytb_t.split('?')[0]
                    except: log_stack.info('FIX:YTB_QUESTION')

                    resp = await self.aio_http.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet'\
                                        +'&fields=items(id%2Ckind%2Csnippet)'\
                                        +'&key={self.conf.get("api", "yt_api")}&id={_ytb_t}')
                    if resp.error:
                        return [False, False]
                    data = json.loads(resp.content.decode('utf8'))
                    _ytb = False
                    for resol in 'maxres', 'standard', 'high':
                        try:
                            _ytb = data.get('items')[0].get('snippet').get('thumbnails').get(resol).get('url')
                        except:
                            continue
                        if not _ytb == None:
                            break
                    return [_ytb, _ytb]

                elif re.search('gfycat.com', url_domain[0]):

                    if 'detail' in _url: _gfy = _url
                    elif 'webm' in _url: return [True, _url]
                    elif 'thumbs' in _url: return [True, _url]
                    else:
                        _gfy = 'https://gfycat.com/gifs/detail/'+_url.split('/')[-1]

                    return [False, _url, '"gifUrl":"(.*?'+_url.split('/')[-1]+'.*?\.gif)"']

                elif re.search('vimeo.com', url_domain[0]):
                    resp = await self.aio_http.get(_url)
                    if resp.error:
                        return [False, False]

                    data = json.loads(resp.content.decode('utf8'))
                    _vimeo_thumb = False
                    try: _vimeo_thumb = data.get('thumbnail_url')
                    except: _vimeo_thumb = False

                    return [_vimeo_thumb, _vimeo_thumb]

                elif re.search('coub.com', url_domain[0]):
                    resp = await self.aio_http.get('https://coub.com/api/v2/coubs/'+_url.split('/')[-1])
                    if resp.error:
                        return [False, False]
                    data = json.loads(resp.content.decode('utf8'))
                    for ver in data.get('image_versions').get('versions'):
                        _coub_image = data.get('image_versions').get('template').format(version=ver).replace('%', '')
                        if ver == 'big':
                            break
                    return [True, _coub_image]

                elif re.search('giphy.com', url_domain[0]):
                    try:
                        _giphy = 'https://media.giphy.com/media/'+_url.split('/')[-1].split('-')[1]+'/giphy_s.gif'
                    except:
                        try:
                            _giphy = 'https://media.giphy.com/media/'+_url.split('/')[-1]+'/giphy_s.gif'
                        except: return [False, False]
                    return [True, _giphy]

                elif re.search('instagram.com', url_domain[0]):
                    return [False, _url, '<meta property="og:image" content="(.*?)"']

                elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:png|jpg|bmp|jpeg|gif)'), _url):
                    return [True, _url]

                elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:webm|mp4|avi|mpeg|3gp)'), _url):
                    return [True, _url]

                #logger.debug(f'new media: {_url}')
                return [False, _url]

            except:
                log_stack.info('check_domain')
                return [False, False]

    async def find_urls(self):
        links = []
        ex_links = []
        try:
            urls = []
            if not self.data:
                return []
            for s in self.recompile:
                r = re.findall(re.compile(s), self.data)
                if r:
                    urls.extend(r)
            urls = sorted(set(urls))
            #logger.info(f'urls: {urls}')

            for _url in urls:
                url = _url.replace('\\u002F', '/').replace('\\u0026', '&').replace('\\', '/')
                if self.what:
                    _ch = await self.check_domain(url)
                    if _ch[0]:
                        links.append(_ch[1])
                    else:
                        if len(_ch) == 3:
                            ex_links.append([_ch[1], _ch[2]])
                else:
                    links.append(url)

            if ex_links:
                _results = await self.aio_http.get_urls([[x[0], None] for x in ex_links])
                for resp, _regex in zip(_results, [x[1] for x in tuple(ex_links)]):

                    if not resp.error:
                        try:
                            links.append(
                                re.findall(
                                    re.compile(_regex),
                                    resp.content.decode('utf8'))[0].replace(
                                    '\u002F', '/').replace(
                                    '\u0026', '&'))
                        except:
                            log_stack.info(f'find_urls.re.compile: {resp.url}')
        except:
            log_stack.info('find_urls', exc_info=True, stack_info=True)

        self.links = links
        return self.ret()

    def ret(self):
        if isinstance(self.links, list):
            return self.links
        elif isinstance(self.links, str):
            return [self.links]
        else:
            return False


class MyWSSMessage:

    def __init__(self, request, ok=False, description='', data=None,
                 method=None, sender=None, server=True):

        self.asyncio_client_loop = None
        self.wss_server_loop = None

        #logger.info(f'req: {request}\n'
        #            f'tp: {type(request)}')
        self.server = True if server else False
        self.client = False if server else True
        if isinstance(request, str):
            request = json.loads(request)

        if isinstance(request, dict):
            _js = request
            self.js = _js
            self.method = _js.get('method')
            self.params = _js.get('params')
            if self.params:
                self.ok = self.params.get('ok')
                self.sender = self.params.get('sender')
                self.description = self.params.get('description')
                self.data = self.params.get('data')
            else:
                self.js.update({'params': []})
                self.ok = False
                self.sender = False
                self.description = False
                self.data = False
        elif request:
            #logger.info(f'd: {data}')
            self.js = {
                'method': method, 'params': {
                    'ok': ok, 'sender': sender, 'description': description, 'data': data
                }
            }
            self.method = method
            self.sender = sender
            self.ok = ok
            self.description = description
            self.data = data
        else:
            self.js = {}
            self.param = None
            self.method = None
            self.sender = None
            self.ok = None
            self.description = None
            self.data = None


class MyWSS:

    methods = {'pull', 'push', 'push_return', 'return', 'open', 'close', 'check', 'status'}

    def __init__(self, sslcert=None, server=None, address=None, client=None, parse_class=None, sender=None, proxy=None):

        self.client_websocket = None
        self.connected_sockets = {}
        self.clients = {}
        self.waits = {}
        self.req_wait = {}

        self.ssl = self.check_ssl(sslcert, server, client)
        self.client = client
        self.ip, self.port = address if address else [False, False]
        self.uri = self.ip + ':' + str(self.port)
        if server:
            self.server = self.wss_server() if server else None
        else:
            self.parse_class = parse_class
            self.sender = sender

        self.proxy = Proxy(proxy)

    def gen_uuid(self):
        return str(uuid.uuid4())

    def check_ssl(self, cert, server, client):
        if not cert:
            return False
        else:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
            localhost_pem = pathlib.Path(cert)
            if server:
                ssl_context.load_cert_chain(localhost_pem)
            elif client:
                ssl_context.load_verify_locations(localhost_pem)
            else:
                return False
            return ssl_context

    def wss_server(self):
        server = websockets.serve(
            self.listener, self.ip, self.port, ssl=self.ssl, max_size=None,
        )
        return server

    async def wss_client(self, restart=True, restart_timeout=10):

        while True:
            try:
                wss_client_socket = await self.client_live()
                await self.client_sms(MyWSSMessage(True, sender=self.sender, method='open').js)
                logger.info(f'open socket with scr_name: {self.sender}')
                break
            except:
                #log_stack.info(f'f.connect')
                if restart:
                    await asyncio.sleep(restart_timeout)
                else:
                    return

        while True:
            try:
                request = await wss_client_socket.recv()
                #logger.info(f'1req: {request}')
                parsed = await self.parse_message(request, wss_client_socket)
                #logger.info(f'parsed: {parsed.js}')
                if self.parse_class:
                    ret = await self.parse_class.work(wss_msg=parsed)
                else:
                    logger.debug('no parse class defined')
            except:
                #log_stack.info(f'restart: {restart}, t:{restart_timeout}')
                if restart:
                    while True:
                        await asyncio.sleep(restart_timeout)
                        try:
                            wss_client_socket = await self.client_live()
                            await self.client_sms(MyWSSMessage(True, sender=self.sender, method='open').js)
                            logger.info(f'restarted. open socket with scr_name: {self.sender}')
                            break
                        except:
                            pass
                            #log_stack.info(f'try restart')
                else:
                    break

    async def client_live(self, **kwargs):
        client_websocket = await websockets.client.connect(
            self.uri, ssl=self.ssl, max_size=None, **kwargs
        )
        self.client_websocket = client_websocket
        return client_websocket

    def wss_client_loop(self, asyncio_client_loop, sl=0, restart=True):
        if sl:
            time.sleep(sl)

        self.asyncio_client_loop = asyncio_client_loop
        asyncio.set_event_loop(asyncio_client_loop)
        try:
            asyncio.get_event_loop().run_until_complete(self.wss_client(restart=restart))
            asyncio.get_event_loop().run_forever()
        except:
            log_stack.info('MyWSS.wss_client_loop')

    def wss_loop(self, wss_server_loop):

        self.wss_server_loop = wss_server_loop
        asyncio.set_event_loop(wss_server_loop)
        try:
            asyncio.get_event_loop().run_until_complete(self.server)
            asyncio.get_event_loop().run_forever()
            #wss_server_loop.run_until_complete(self.server)
            #asyncio.run(self.server())
        except:
            log_stack.info('MyWSS.wss_loop')

    async def sms(self, js={}, socket=None, js_id=None):
        #logger.info(f'js: {js}')
        return await self.send_request(js, socket, js_id=js_id)

    async def client_return(self, js, wss_socket):
        try:
            pz = self.make_request(js)
            #logger.info(f'pz.make: {pz}')
            z = await wss_socket.send(pz)

            #logger.info(f'z.pox: {z}')
            return z
        except:
            log_stack.info('client_sms')

    async def client_sms(self, js, wss_socket=None, js_id=None):

        try:
            if not wss_socket:
                wss_socket = self.client_websocket

            if not wss_socket:
                return MyWSSMessage(True, ok=False, description='socket not open', sender='self')

            #logger.info(f'1100.js: {js}')
            await wss_socket.send(self.make_request(js, js_id=js_id))
            #logger.info(f'11')
            apx = await wss_socket.recv()
            #logger.info(f'222.apx: {apx}')
            return apx
        except:
            log_stack.info('client_sms')

    async def send_request(self, data, socket=None, js_id=None):

        if not socket:
            async with websockets.connect(
                    self.uri, ssl=self.ssl, max_size=None,
            ) as websocket:
                await websocket.send(self.make_request(data, js_id=js_id))
                return await websocket.recv()
        else:
            return await socket.send(self.make_request(data, js_id=js_id))

    def make_request(self, my_wss_message, js_id=None):
        return json.dumps(
            {
                "jsonrpc": '2.0',
                **my_wss_message,
                "id": js_id if js_id else self.gen_uuid()})

    async def listener(self, websocket, path):
        try:
            request = await websocket.recv()
            #logger.info(f'serv, request: {request}')

            data, request_id = await self.parse_message(json.loads(request).copy(), websocket)
            #logger.info(f'data: {data}, ')
            sender = data.get('params').get('sender')

            if data.get('method') == 'open':
                if sender not in self.connected_sockets:
                    self.connected_sockets[sender] = set()

                self.connected_sockets[sender].add(websocket)
                await websocket.send(self.make_request(data, js_id=request_id))

                if self.clients[sender]['new']:
                    logger.debug('pull when open')
                    logger.debug(f'ident: {sender}')
                    logger.debug(f'server pull: {self.clients[sender]}')
                    new = self.clients[sender]['new']
                    tasks = list(self.clients[sender]['tasks'])

                    self.clients[sender]['new'] = False
                    self.clients[sender]['tasks'].clear()

                    await websocket.send(self.make_request(MyWSSMessage(True, ok=new, data=tasks).js, js_id=request_id))

                while str(data.get('method')) != 'close':
                    try:
                        request = await websocket.recv()
                        data, request_id = await self.parse_message(json.loads(request), websocket)
                        await websocket.send(self.make_request(data, js_id=request_id))
                    except:
                        log_stack.info(f'on wait close')
                        break

                self.connected_sockets[sender].remove(websocket)
                logger.debug(f'socket closed sender: {sender} address: {websocket.remote_address}')
                return

            #logger.info(f'serv, data: {data}')
            await websocket.send(self.make_request(data, js_id=request_id))
        except:
            try:
                if websocket in self.connected_sockets[sender]:
                    self.connected_sockets[sender].remove(websocket)
            except:
                pass
            log_stack.info('listener')

    async def parse_message(self, request, websocket=None):
        try:

            if self.client:
                logger.debug('parse_message.client')
                return MyWSSMessage(json.loads(request))

            request_id = request.get('id')
            request_params = request.get('params')
            request_method = request.get('method')

            #logger.info(f'req_id: {request_id}\nself.req_wait: {self.req_wait}')
            if request_id in self.req_wait:
                self.req_wait[request_id] = request
                return MyWSSMessage(True, ok=True).js, request_id

            if request_method not in self.methods:
                return MyWSSMessage(True, ok=False, description='method not allowed').js, request_id

            client_ip, client_port = websocket.remote_address
            #logger.info(f'params: {request_params}')
            request_sender = request_params.get('sender')
            request_ident = request_sender

            while self.waits.get(request_ident):
                logger.info(f'wait from {request_ident} on ip:{client_ip}')
                await asyncio.sleep(1)

            request_data = request_params.get('data')

            if request_ident not in self.clients:
                self.clients[request_ident] = {'connections': [], 'new': False, 'tasks': deque()}
                self.clients[request_ident]['connections'].append({'ip': client_ip, 'socket': False})

            if request_method == 'pull':
                logger.info(f'pull ident: {request_ident}')
                logger.info(f'server pull: {self.clients[request_ident]}')
                new = self.clients[request_ident]['new']
                tasks = list(self.clients[request_ident]['tasks'])

                self.clients[request_ident]['new'] = False
                self.clients[request_ident]['tasks'].clear()

                return MyWSSMessage(True, ok=new, data=tasks).js, request_id

            if request_method == 'return':
                logger.info(f'return: {self.clients[request_ident]}')
                return MyWSSMessage(request).js, request_id

            if request_method == 'open':
                return MyWSSMessage(True, ok=True, description='opened', method=request_method, sender=request_params.get('sender')).js, request_id

            if request_method == 'close':
                return MyWSSMessage(True, ok=True, description='closed', method=request_method, sender=request_params.get('sender')).js, request_id

            if request_method == 'check' or request_method == 'status':

                if request_params.get('sender') in self.connected_sockets:
                    con_clients = list(self.connected_sockets[request_params.get('sender')])
                else:
                    con_clients = tuple()

                if request_method == 'check':
                    return MyWSSMessage(
                        True, ok=True, description='clients',
                        data=len(con_clients),
                        method=request_method, sender=request_params.get('sender')).js, request_id

                elif request_method == 'status':
                    ret_text = ''
                    for sender, _sockets in self.connected_sockets.items():
                        ret_text += f'{sender}\n'
                        for _socket in _sockets:
                            pass

                    if not ret_text:
                        ret_text = 'no clients'

                    return MyWSSMessage(
                        True, ok=True, description='status',
                        data=ret_text,
                        method=request_method, sender=request_params.get('sender')).js, request_id

            self.waits[request_ident] = True
            if request_method == 'push' or request_method == 'push_return':
                try:
                    for d in request_data:
                        if request_ident in self.connected_sockets:
                            for sock in self.connected_sockets[request_ident]:
                                _send_to_sockets = True
                                if request_method == 'push':
                                    await self.send_request(MyWSSMessage(True, ok=True, data=[d]).js, sock)
                                elif request_method == 'push_return':
                                    #p = await self.client_return(MyWSSMessage(True, ok=True, data=[d]).js, sock)
                                    #logger.info(f'pre11')

                                    self.req_wait[request_id] = False
                                    p = await self.send_request(
                                        MyWSSMessage(True, ok=True, method='push', data=[d]).js, sock, js_id=request_id)

                                    #logger.info(f'11p.imp: {p}, req_id: {request_id}')
                                    while not self.req_wait[request_id]:
                                        await asyncio.sleep(1)

                                    answer = self.req_wait[request_id]
                                    #logger.info(f'ex got request after wait: {answer}')
                                    del self.req_wait[request_id]

                                    #pp = await sock.recv()
                                    #logger.info(f'ppp.!!!: {pp}')
                                    #zp = await self.client_return(MyWSSMessage(True, ok=True, data=[d]).js, sock)
                                    #logger.info(f'12p: {zp}')

                                    self.waits[request_ident] = False
                                    return MyWSSMessage(answer, ok=True).js, request_id

                        else:
                            self.clients[request_ident]['tasks'].append(d)
                except:
                    log_stack.info('tasks.exc')

                logger.debug(f'push ident: {request_ident}')
                self.waits[request_ident] = False
                if request_data:
                    self.clients[request_ident]['new'] = True

                logger.debug(self.clients)
                return MyWSSMessage(True, ok=True).js, request_id
        except:
            log_stack.info('MyWSS')

try:
    @responses.activate
    def requests_simulate(url='http://ggg', code=200, text='simulate',
                          js={}, content_type='text/plain', proxy=None, path=None, tmp_dir=''):

        if js:
            responses.add(responses.GET, url,
                          json=js, status=code)
        else:
            responses.add(responses.GET, url,
                          body=text, status=code,
                          content_type=content_type)

        _resp = requests.get(url)

        return MergeResp(
            _resp.text, _resp.content, _resp.headers, _resp.status_code, _resp.url,
            path=tmp_dir+path if path \
                                 and isinstance(path, str) \
                else MyHttpUtils().make_path(url, tmp_dir=tmp_dir) if path else None,
            proxy=proxy, error=False
        )


except:
    pass
