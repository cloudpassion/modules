import os
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

import bjdata as bj
import ujson as json

from pathlib import Path
from sanic.response import html
from datetime import datetime, timedelta

from atiny.http.aio import MyHttp
from config import secrets, settings
from log import logger, log_stack
from kinozaltv import KinozalSite

from .tor2me import TrackerHelper
from ..abstract import AbstractServer


bencode.Bencode(encoding='utf8')


class Info(
    TrackerHelper,
    AbstractServer,
):

    check_date = timedelta(days=30)

    def info_return(self):
        return html(
            b'always_ok'
        )

    async def info(self, request, announce_request=None):

        try:
            if not announce_request:
                info_hash = request.args['info_hash'][0]
        except:
            return self.info_return()

        if announce_request:
            query_args = self.get_query_args(announce_request)
            info_hash = self.get_info_hash(query_args=query_args)

        else:
            query_args = None

        info_hash = info_hash.lower()
        logger.info(f'{info_hash=}')

        if os.path.isfile(
                f'{settings.kinozal.details_dir}/force/{info_hash}'
        ):
            force = True
        else:
            force = False

        if not force and os.path.isfile(f'{settings.kinozal.details_dir}/not_kinozal/{info_hash}'):
            logger.info(f'no_kinozal')
            return self.info_return()

        if not force and os.path.isfile(f'{settings.kinozal.details_dir}/skip/{info_hash}'):
            logger.info(f'skip')
            return self.info_return()

        torrent_path = f'{settings.kinozal.hashes_dir}/{info_hash}'
        if os.path.isfile(torrent_path):
            with open(torrent_path, 'rb') as tr:
                # data = json.loads(tr.read())
                data = bj.loadb(tr.read())
        else:
            logger.info(f'no torrent')
            return self.info_return()

        if 'comment' not in data:

            logger.info(f'no comment')
            return self.info_return()

        if 'kinozal' in data['comment']:
            pass
        else:
            Path(f'{settings.kinozal.details_dir}/not_kinozal/{info_hash}').touch()
            logger.info(f'no kinozal')
            return self.info_return()

        details_id = data['comment'].split('=')[1]
        if os.path.isfile(
                f'{settings.kinozal.details_dir}/force/{details_id}'
        ):
            force = True

        if os.path.isfile(f'{settings.kinozal.details_dir}/page/{details_id}'):
            mod_time = os.path.getmtime(
                f'{settings.kinozal.details_dir}/page/{details_id}'
            )
            mod_time = datetime.fromtimestamp(mod_time)
            if not force and datetime.now() - mod_time < self.check_date:
                logger.info(f'no time')
                return self.info_return()

        if force:
            for tp in ['force', 'not_kinozal']:
                for key in [details_id, info_hash]:
                    try:
                        os.remove(f'{settings.kinozal.details_dir}/{tp}/{key}')
                    except FileNotFoundError:
                        pass

        kn = KinozalSite()
        check = await kn.get_details(details_id)
        if not check:
            logger.info(f'maybe not exists')
            return self.info_return()

        logger.info(f'{kn.who_full}')
        if not kn.who_full:
            logger.info(f'no_full: {kn.link}')
            return self.info_return()

        if secrets.nickname not in kn.who_full:
            await self.complete_to_tracker(info_hash, query_args, details_id)
        else:
            logger.info(f'nick exists')
            with open(f'{settings.kinozal.details_dir}/page/{details_id}', 'w') as fw:
                fw.write('changed')

        return self.info_return()

    async def complete_to_tracker(
            self, info_hash, query_args, details_id,
    ):

        if query_args:
            peer_port = query_args['port']
            peer_id = query_args['peer_id']
            uploaded = query_args['uploaded']
            downloaded = query_args['downloaded']
        else:
            # peer_port = 53312
            uploaded = 0
            downloaded = 0

        peer_port = random.randint(1024, 65535)
        peer_id = f'{"".join(peer_id[0:7])}' \
                  f'-' + \
                  ''.join(
                      [
                          random.choice(
                              self.random_words
                          ) for _ in range(12)
                      ]
                  )

        data = {
            'info_hash': binascii.a2b_hex(info_hash),
            'peer_id': peer_id,
            'port': peer_port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': 0,
            'event': 'completed',
            'semaphore': 1,
        }
        url = f'http://tor2merun.local/announce?{urllib.parse.urlencode(data)}'
        logger.info(f'{url}')

        # kn = KinozalSite()
        http = MyHttp(
            # proxy=kn.proxy, ssl_cert=kn.proxy_ssl_cert,
        )
        resp = await http.get(
            url
        )
        logger.info(f'{resp.status}, {resp.content}')
        if resp.status == 200:
            with open(f'{settings.kinozal.details_dir}/page/{details_id}', 'w') as fw:
                fw.write('changed')

        # &downloaded=0&left=0&corrupt=0&
        # key=ED470F60&numwant=200&compact=1&no_peer_id=1
        # &supportcrypto=1&redundant=0

    async def load_info(self):
        app = self.app

        @app.route(
            'info'
        )
        async def sanic_info(request: sanic.Request):
            return await self.info(request)
