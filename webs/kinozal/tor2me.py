import asyncio
import binascii
import time
import urllib
import urllib.parse
import bencodepy as bencode
import itertools
import random
import aiohttp
import sanic
import pickle
import base64
import string

from sanic.response import html
from datetime import datetime, timedelta

from atiny.http import MyHttp
from config import secrets, settings
from log import logger, log_stack

from ..abstract import AbstractServer


bencode.Bencode(encoding='utf8')


class TrackerHelper:

    def get_query_args(self, request):
        query_args = dict(x.split("=") for x in request.query_string.split("&"))
        return query_args

    def get_info_hash(self, request=None, query_args=None):
        if not query_args:
            query_args = self.get_query_args(request)

        info_hash = urllib.parse.unquote_to_bytes(query_args['info_hash'])
        info_hash = binascii.b2a_hex(info_hash).decode('utf8')
        return info_hash


class Tor2Me(
    TrackerHelper,
    AbstractServer,
):

    random_words = string.ascii_uppercase + \
                        string.ascii_lowercase + \
                        string.digits
    tracker_passkey = secrets.passkey.kinozal
    passkey_path: str

    tracker_hosts = [
            f'http://tr{x}.{host}' for x, host in itertools.product(range(0, 6), [
                'torrent4me.com',
                'tor2me.info',
                'tor4me.info',
            ])
        ]

    dht = {
        'pfru': f'http://{settings.http.domain}/adht?var=pfru',
        'pfvps': f'http://{settings.http.domain}/adht?var=pfvps',
        'isp': f'http://{settings.http.domain}/adht?var=isp',
    }
    extra_dht = {
        dht['pfru'],
        dht['pfvps'],
    }
    proxies = {
        'pfru': 'http://192.168.55.165:45010',
        'pfvps': 'http://192.168.55.165:45011',
        'isp': 'http://192.168.55.165:36101',
    }
    extra_proxies = [
        proxies['pfru'],
        proxies['pfvps'],
        proxies['isp'],
    ]
    extra_ports = {
        # seed
        # sbox_big qbit pfru
        53312: {
            'proxies': [
                # proxies['pfru'],
                proxies['pfvps'],
            ],
            'dht': [
                # proxies['pfru'],
                proxies['pfvps'],
            ],
            'ports': [53312, ],
        },
        # seedbox qbit pfvps
        57288: {
            'proxies': [
                proxies['pfvps'],
            ],
            'dht': [
                # proxies['pfru'],
                proxies['pfvps'],
            ],
            'ports': [57288, ],
        },
        # download
        # sbox_big utorrent download
        46288: {
            'proxies': [
                    # proxies['pfru'],
                    proxies['pfvps'],
                ],
            'dht': [
                # proxies['pfru'],
                proxies['pfvps'],
            ],
            'ports': [46288, ], #46289, 46290, ],
        },
        # seedbox utorrent download
        27843: {
            'proxies': [
                # proxies['pfru'],
                proxies['pfvps'],
            ],
            'dht': [],
            'ports': [27843, ], #27844, 27845, ],
        }

    }
    cache_timeout = timedelta(minutes=25)
    cache: dict
    # {
    #     'info_hash': {
    #         'time': datetime.now(), 'response': resp.content,
    #         'tracker': tracker_host,
    #     }
    # }
    check_proxies = [
        'http://192.168.55.165:34010',
        'http://192.168.55.165:34011',
        'http://192.168.55.165:34012',
        'http://192.168.55.165:34013',
        'http://192.168.55.165:34014',
        'http://192.168.55.165:34015',
    ]

    check_urls = [
        'http://this.com/',
        'http://google.com',
        'http://www.infobyip.com/',
        'http://cloudflare.com',
        'http://duckduckgo.com/',
    ]

    info_hash_semaphore = {}

    async def load_redis_cache(self):
        try:
            self.redis_conn.set("tor2me_cache_dict", pickle.dumps({}))
            self.cache = pickle.loads(
                self.redis_conn.get('tor2me_cache_dict')
            )
            # logger.info(f'{self.cache=}')
        except:
            self.cache = {}

    async def check_cache(self, info_hash, peer_port, text=None):

        have_cache = {}
        if info_hash in self.cache:
            have_cache = self.cache[info_hash].get(peer_port)

        if have_cache:

            need_fresh = True
            prev_time = have_cache.get('time')

            if datetime.now() - prev_time < self.cache_timeout:
                need_fresh = False

            if not need_fresh:
                return html(
                    base64.b64decode(
                        have_cache['response']
                    ),
                    headers={
                        'Connection': 'close',
                    }
                )

        if text:
            return await self.tracker_error(text=text)

    async def tracker_error(
            self, info_hash=None, peer_port=None, text=None
    ):

        if info_hash and peer_port:
            cache = await self.check_cache(info_hash, peer_port)
            if cache:
                return cache

        if not text:
            text = 'unregistered error'

        return html(
            bencode.encode(
                {'failure reason': text}
            ),
            headers={
                'Connection': 'close',
            },
            status=404,
        )

    async def announce_semaphore(self, request, force=False):

        logger.info(f'{request.method}:{request.query_string}, {force=}')

        if not request.query_string:
            return await self.tracker_error(text='no query_string')

        try:
            query_args = self.get_query_args(request)
        except Exception:
            return await self.tracker_error(request, text='query stack')

        info_hash = self.get_info_hash(query_args=query_args)
        logger.info(f'{info_hash=}')
        peer_port = int(query_args['port'])

        if 'semaphore' in query_args or force:
            return await self.announce(
                request, query_args, info_hash, peer_port, force=force
            )
        else:
            sem = self.info_hash_semaphore.get(f'{peer_port}_{info_hash}')
            if not sem:
                sem = asyncio.Semaphore(1)
                self.info_hash_semaphore[f'{peer_port}_{info_hash}'] = sem

            async with sem:
                return await self.announce(
                    request, query_args, info_hash, peer_port, force=force
                )

    async def announce(self, request, query_args, info_hash, peer_port, force):

        try:
            event = query_args['event']
        except KeyError:
            event = None

        left = int(query_args['left'])
        peer_id = query_args['peer_id']

        cache = await self.check_cache(info_hash, peer_port)
        if not force and cache:
            logger.info(f'return_cashed for {info_hash=}')
            return cache

        keys_to_del = ['key', 'ip', 'numwant', 'semaphore', ]
        if event:
            if event == 'stopped' and cache:
                return cache
            else:
                keys_to_del.append('event')

        # check = info_hash == ''.lower()
        # logger.info(info_hdash)
        # logger.info(''.lower())
        # logger.info(f'{check=}')
        # return await self.tracker_error(text='dev')
        good_proxy = None
        while True:
            random.shuffle(self.check_proxies)

            for check_proxy in self.check_proxies:
                http = MyHttp(
                    timeout=aiohttp.ClientTimeout(total=12),
                    proxy=check_proxy, log=False,
                )
                resp = await http.head(
                    random.choice(self.check_urls)
                )
                if resp.error:
                    continue

                if resp.status == 200 or resp.status == 301 or resp.status == 302:
                    good_proxy = check_proxy
                    break

            else:
                logger.info(f'no working check_proxy')
                await asyncio.sleep(1)
                continue

            break

        random.shuffle(self.tracker_hosts)
        if self.cache.get(info_hash) and self.cache[info_hash].get('tracker'):
            tracker_hosts = [
                self.cache[info_hash]['tracker'],
                *self.tracker_hosts,
            ]
        else:
            tracker_hosts = self.tracker_hosts

        # keys delete
        announce_path = request.query_string
        for key in keys_to_del:
            if key not in query_args:
                continue
            announce_path = announce_path.replace(
                f'&{key}={query_args[key]}', ''
            )

        good_resp = None
        for tracker_host in tracker_hosts:

            http = MyHttp(
                timeout=aiohttp.ClientTimeout(total=6),
                proxy=good_proxy, log=False,
            )

            cache = await self.check_cache(
                request, info_hash,
            )
            if cache:
                break

            resp = await http.get(
                f'{tracker_host}/{self.passkey_path}&{announce_path}',
                headers={
                    'user-agent': request.headers['user-agent'],
                    'accept-encoding': 'gzip',
                }
            )
            logger.info(f'tracker:{info_hash}:{resp.status}:{resp.content[:15]}')
            if resp.error:
                continue

            if resp.status != 200:
                continue

            data = bencode.bdecode(
                resp.content
            )
            # logger.info(f'main:{data=}')

            fail = data.get(b'failure reason')
            if fail:
                continue

            good_resp = resp
            break
        else:
            cache = await self.check_cache(
                info_hash, peer_port,
                text='all tracker failure',
            )
            return cache

        if good_resp:

            if event and event != 'completed' and left == 0:
                await self.info(None, announce_request=request)

            if not self.cache.get(info_hash):
                self.cache[info_hash] = {}

            if not self.cache[info_hash].get(peer_port):
                self.cache[info_hash][peer_port] = {}

            self.cache[info_hash]['tracker'] = tracker_host
            self.cache[info_hash][peer_port] = {
                        'time': datetime.now(),
                        'response': base64.b64encode(good_resp.content),
                    }

            if peer_port in self.extra_ports:
                extra_proxies = self.extra_ports[peer_port]['proxies']
            else:
                extra_proxies = []

            for extra_proxy in extra_proxies:

                if event and event == 'stopped':
                    continue

                # if left == 0:
                #     continue

                http = MyHttp(
                    timeout=aiohttp.ClientTimeout(total=12),
                    proxy=extra_proxy, log=False,
                )

                for new_port in self.extra_ports[peer_port]['ports']:

                    if new_port != peer_port:
                        cache = await self.check_cache(
                            info_hash, new_port
                        )
                        if cache:
                            continue

                    # new_peer_id = f'{"".join(peer_id[0:7])}' \
                    #               f'-' + \
                    #               ''.join(
                    #                   [
                    #                       random.choice(
                    #                           self.random_words
                    #                       ) for _ in range(12)
                    #                   ]
                    #               )
                    new_peer_id = peer_id

                    new_path = announce_path.replace(
                        f'&port={peer_port}', f'&port={new_port}'
                    ).replace(
                        f'&peer_id={peer_id}', f'&peer_id={new_peer_id}'
                    )
                    extra_resp = await http.get(
                        f'{tracker_host}/{self.passkey_path}&'
                        f'{new_path}',
                        headers={
                            'user-agent': request.headers['user-agent'],
                            'accept-encoding': 'gzip',
                        }
                    )
                    logger.info(f'{extra_resp.status=}:{new_path},'
                                f'{extra_resp.content},'
                                f'{extra_resp.proxy.aio_str}')

                    if extra_resp.error:
                        continue

                    if extra_resp != 200:
                        continue

                    # data = bencode.bdecode(
                    #     extra_resp.content
                    # )
                    # logger.info(f'sec:{data=}')

                    if new_port == peer_port:
                        continue

                    if not self.cache[info_hash].get(new_port):
                        self.cache[info_hash][new_port] = {}

                    self.cache[info_hash][new_port] = {
                        'time': datetime.now(),
                        'response': base64.b64encode(extra_resp.content),
                    }

            self.redis_conn.set("tor2me_cache_dict", pickle.dumps(self.cache))

            return html(
                resp.content,
                headers={
                    'Connection': 'close',
                }
            )

        else:
            cache = await self.check_cache(
                info_hash, peer_port,
                text='no good resp',
            )
            return cache

    async def load_tor2me(self):
        app = self.app

        await self.load_redis_cache()

        if len(self.tracker_passkey) == 32:
            self.passkey_path = f'announce.php?passkey={self.tracker_passkey}'
        else:
            self.passkey_path = f'ann?uk={self.tracker_passkey}'

        @app.route(
            'announce'
        )
        async def sanic_announce(request: sanic.Request):
            return await self.announce_semaphore(request)

        @app.route(
            'fannounce'
        )
        async def sanic_fannounce(request: sanic.Request):
            return await self.announce_semaphore(request, force=True)
