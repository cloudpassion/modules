import os
import asyncio

from base64 import b64decode
from typing import Union

try:
    import ujson as json
except ImportError:
    import json

from atiny.reos.dir.create import create_dir
from config import secrets
from log import logger, log_stack

from ..tgx.hotpicks import TGxHotPicks, TgxHotPicksItem
from ..tgx.details import TgxDetailsPage

from ..getmov import GetMovies
from .db import SkipDB

# TODO: rewrite tg
from otg import tg_send_loop, tg_send_media
from atiny.http import MyHttp

from .default import MonMovDefault


class TgxMonitor(
    MonMovDefault,
):
    db: SkipDB
    skip_names: list
    skip_imdb: list

    def __init__(self):
        self.init_db()

    def init_db(self):
        self.db = SkipDB()
        self.skip_names = self.db.fdb_get_skip_names()
        self.skip_imdb = self.db.fdb_get_skip('imdb')

    async def hot_picks_releases(
            self, year, years=None,
    ):

        items = []
        for cat in (1, 3):

            while True:
                try:
                    hotpicks_page = TGxHotPicks()
                    await hotpicks_page.tgx_get_hot_picks(
                        cat=cat
                    )
                    break
                except Exception:
                    log_stack.error('stack')
                    await asyncio.sleep(10)

            if not hotpicks_page.items:
                break

            items.extend(hotpicks_page.items)
            await asyncio.sleep(5)

        for item in items:
            item: TgxHotPicksItem

            check = await self.tgx_check_notify(
                item=item, titles=None,
                years=years,
            )
            if not check:
                continue

            await self.tgx_notify_release(item)

    async def tgx_check_notify(
            self, item: Union[TgxHotPicksItem],
            titles, years,
    ):

        if item.name in self.skip_names:
            return

        if years is not None:
            if item.year not in years:
                return

        skip = True

        if titles is not None:
            if item.title and item.title in titles:
                logger.info(f'{item.title=} in titles')
                skip = False

        else:
            skip = False

        if skip:
            return False
        else:
            return True

    async def tgx_notify_release(
            self,
            item: Union[TgxHotPicksItem],
    ):

        if isinstance(
                item, (
                        TgxHotPicksItem,
                )
        ):
            details_page = TgxDetailsPage(id=item.id, pre_item=item)
            await details_page.get_details()
        else:
            details_page = item

        if details_page.imdb and details_page.imdb in self.skip_imdb:
            logger.info(f'{details_page.imdb=} imdb already parsed')
            self.db.fdb_add_parsed(
                f'{details_page.name}|{details_page.link.split("/")[-1]}'
            )
            self.skip_names.append(f'{details_page.name}')
            return

        logger.info(f'{details_page.link}')

        # TODO: rewrite this *sheet
        jpgs = await self.download_images(images=[details_page.image, ])
        tr = 0
        br = False
        while True:
            tr += 1
            try:
                tg_send_loop(
                    (
                        details_page.link,
                        details_page.name,
                        f'{details_page.link}\n'
                        f'{details_page.info_hash.lower()}\n\n'
                        f'{details_page.description}\n\n'
                        f'{details_page.magnet}\n\n',
                        [False, ''],
                        [
                            True if jpgs else False,
                            'file',
                            jpgs,
                        ],
                        False
                    )
                )
                break
            except Exception:
                log_stack.error('tg stuck')
                await asyncio.sleep(10)

            if tr >= 10:
                br = True
                break

        if br:
            return

        tr = 0
        br = False
        while True:
            try:

                http = MyHttp()

                magnet = details_page.magnet if hasattr(
                    details_page, 'magnet'
                ) else f'magnet:?xt=urn:btih:{details_page.info_hash.lower()}'
                resp = await http.get(
                    url=f'http://{secrets.m2t.host}/?'
                        f'apikey={secrets.m2t.api}&'
                        f'magnet={magnet}',
                )

                if resp.error or resp.status != 200:
                    logger.info(f'check 55')
                    await asyncio.sleep(10)
                    continue

                js = json.loads(resp.content.decode('utf8'))
                status = js.get('status')
                logger.info(f'{status=}')
                if status != 'success':
                    await asyncio.sleep(10)
                    continue

                # logger.info(f'{js=}')
                t_data = b64decode(js.get('torrent_data'))
                # logger.info(f'{t_data=}')

                create_dir('torrents')
                t_file = f'torrents/{details_page.info_hash}.torrent'
                with open(t_file, 'wb') as wb:
                    wb.write(t_data)

                tr += 1
                torrent = open(t_file, 'rb')
                tg_send_media(
                    secrets.m2t.cid, torrent,
                    f'{details_page.link}\n'
                    f'https://www.imdb.com/title/{details_page.imdb}/\n'
                    f'{details_page.name}\n'
                    f'{details_page.info_hash.lower()}\n\n',
                    media='document',
                )
                torrent.close()

                break
            except Exception:
                log_stack.error('tg stuck')
                await asyncio.sleep(10)

            if tr >= 10:
                br = True
                break

        if br:
            return

        self.db.fdb_add_parsed(
            f'{details_page.name}|{details_page.link.split("/")[-1]}'
        )
        self.skip_names.append(f'{details_page.name}')

        if details_page.imdb:
            self.db.fdb_add_imdb(
                f'{details_page.imdb}'
            )
            self.skip_imdb.append(f'{details_page.imdb}')

        await asyncio.sleep(1)
