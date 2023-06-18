import os
import asyncio

from typing import Union

from log import logger, log_stack

from ..kinozaltv.details import DetailsPage
from ..kinozaltv.browse import BrowsePage, BrowseItem
from ..kinozaltv.top import TopPage, TopItem

from ..getmov import GetMovies
from .db import SkipDB

# TODO: rewrite tg
from otg import tg_send_loop
from atiny.http import MyHttp


class KinozalMonitor:
    db: SkipDB
    skip_names: list
    skip_imdb: list

    def __init__(self):
        self.init_db()

    def init_db(self):
        self.db = SkipDB()
        self.skip_names = self.db.fdb_get_skip_names()
        self.skip_imdb = self.db.fdb_get_skip('imdb')

    async def deep_releases(self, title_year, start=None):

        year = title_year
        pp_year = year - 2
        pre_year = year - 1
        next_year = year + 1

        years = [
            pp_year,
            pre_year, year,
            # next_year
        ]

        titles = GetMovies().get_year_titles(title_year)
        if not titles:
            return

        for title in titles:

            logger.info(f'search in {title_year=} for {title=}')

            if start:
                if title.lower() != start.lower():
                    logger.info(f'skip {title=} for {start=}')
                    continue

                start = False

            for year in years:

                await self._deep_release_title(
                    title, year, titles, years
                )
                await asyncio.sleep(1)

    async def _deep_release_title(
            self, title, year, titles, years
    ):

        items = []

        for category in ['films', 'serials', 'cartoons']:
            logger.info(f'search in {category}')

            browse_page = BrowsePage()
            await browse_page.get_browse(
                search=title, year=year,
                category=category,
            )
            await asyncio.sleep(0.3)

            if not browse_page.items:
                continue

            items.extend(browse_page.items)

        # for page in range(1, browse_page.pages):
        #     browse_page = BrowsePage()
        #     await browse_page.get_browse(
        #         search='ghosted', year=year,
        #         page=page,
        #     )
        #
        #     if not browse_page.items:
        #         continue
        #
        #     items.extend(browse_page.items)

        for item in items:
            item: BrowseItem
            logger.info(f'{item=}')

            check = await self.check_notify(
                item=item, titles=titles,
                years=years,
            )
            if not check:
                continue

            await self.notify_release(item)

    async def check_notify(
            self, item: Union[BrowseItem, DetailsPage, TopItem],
            titles, years,
    ):

        if item.name in self.skip_names:
            # logger.info(f'{item.name=} already parsed')
            return

        if '/ РУ' in item.name:
            # logger.info(f'skip {item.name=} RU')
            return

        if '/ TS' in item.name:
            # logger.info(f'skip translate {item.name=}')
            return

        if years is not None:
            if item.year not in years:
                # logger.info(f'{item.year=} not in {years=}')
                return

        skip = True

        if titles is not None:
            if item.title in titles:
                logger.info(f'{item.title=} in titles')
                skip = False

            if item.en_title in titles:
                logger.info(f'{item.en_title=} in titles')
                skip = False
        else:
            skip = False

        if skip:
            return False
        else:
            return True

    async def notify_release(
            self,
            item: Union[BrowseItem, DetailsPage, TopItem]
    ):

        if isinstance(item, (BrowseItem, TopItem)):
            details_page = DetailsPage(id=item.id)
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

        # TODO: rewrite tg
        screens = details_page.screens if details_page.screens else []
        jpgs = []
        for _n, scr in enumerate([
            details_page.image,
            *screens
        ]):
            n = _n + 1
            if not scr:
                try:
                    os.remove(f'{n}.jpg')
                except Exception:
                    pass

                continue

            if len(jpgs) >= 10:
                break

            http = MyHttp(
                save_cache=True, save_headers=False
            )
            resp = await http.get(
                url=scr, tmp_dir='.', path=f'{n}.jpg'
            )
            if not resp.error and resp.status == 200:
                jpgs.append(f'{n}.jpg')
            else:
                try:
                    os.remove(f'{n}.jpg')
                except Exception:
                    pass

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
                        f'{details_page.roles_data.get("text")}\n\n'
                        f'{details_page.about}\n\n'
                        f'{details_page.release}\n\n'
                        f'{details_page.specs}\n\n'
                        f'magnet:?xt=urn:btih:{details_page.info_hash.lower()}',
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

    async def main_releases(self, year):

        p_year = year - 1
        pp_year = p_year - 1
        next_year = year + 1

        years = [pp_year, p_year, year, next_year]

        items = []
        for category in ['films', 'serials', 'cartoons']:
            for page in range(0, 10):
                logger.info(f'search in {category} on {page=}')

                while True:
                    try:
                        browse_page = BrowsePage()
                        await browse_page.get_browse(
                            category=category, page=page,
                        )
                        break
                    except Exception:
                        log_stack.error('stack')
                        await asyncio.sleep(10)

                items.extend(browse_page.items)
                await asyncio.sleep(1)

            await asyncio.sleep(5)

        for release_year in years:

            logger.info(f'main rel: {release_year=}')
            titles = GetMovies().get_year_titles(year=release_year)
            if not titles:
                logger.info(f'no titles for {release_year=}')
                continue

            logger.info(f'{len(items)=}')
            for item in items:
                item: BrowseItem

                check = await self.check_notify(
                    item=item, titles=titles,
                    years=years,
                )
                if not check:
                    continue

                await self.notify_release(item)

    async def top_releases(
            self, year, years, uploaded_in,
    ):

        items = []
        for category in [
            # 'best_shares',
            'films',
            'serials', 'cartoons',
        ]:
            for uploaded in uploaded_in:
                for sort in ['peers', 'seeds', 'comments']:

                    for page in range(0, 20):
                        logger.info(f'search in {category} '
                                    f'on {uploaded} '
                                    f'with sorting by {sort} '
                                    f'in {page=}')

                        while True:
                            try:
                                top_page = TopPage()
                                await top_page.get_top(
                                    category=category,
                                    sort=sort,
                                    uploaded=uploaded,
                                    page=page,
                                    release_years=year,
                                )
                                break
                            except Exception:
                                log_stack.error('stack')
                                await asyncio.sleep(10)

                        if not top_page.items:
                            break

                        items.extend(top_page.items)
                        await asyncio.sleep(1)

                    await asyncio.sleep(5)

        for item in items:
            item: TopItem

            check = await self.check_notify(
                item=item, titles=None,
                years=years,
            )
            if not check:
                continue

            await self.notify_release(item)
