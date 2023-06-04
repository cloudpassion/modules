import re
import os

from bs4 import BeautifulSoup, Tag
from collections import defaultdict

from atiny.http.utils import MyHttpUtils
from config import settings
from log import logger, log_stack

from ..http import Http
from ..details import DetailsPage
from ..find_vars import KinozalVarsFinder


class BrowseItem(
    KinozalVarsFinder,
):

    keys = [
        'name', 'link', 'category', 'id',
        'title', 'en_title', 'ru_title', 'year', 'translate', 'ripped',
        'seeds', 'peers',
    ]

    id: int
    name: str
    link: str
    category: str
    title: str
    en_title: str
    ru_title: str
    year: int
    translate: str
    ripped: str
    seeds: int
    peers: int


class BrowsePage(
    Http,
    KinozalVarsFinder,
):

    keys = [
        'items',
    ]

    items: list = []
    pages: int = 0

    wheres = {
        'everywhere': 0,
    }

    categories = {
        'all': 0,
        'films': 1002,
        'serials': 1001,
        'cartoons': 1003,
    }

    gif_categories = defaultdict(
        lambda: 'unknown',
        {
            '8.gif': 'comedy',
            '15.gif': 'thriller.detective',
            '17.gif': 'drama',
            '20.gif': 'anime',
            '35.gif': 'melodrama',
        }
    )

    formats = {
        'all': 0,
    }

    whens = {
        'always': 0
    }

    sorts = {
        'default': 0 # when publish
    }

    sorts_order = {
        'decrease': 0,
        'increase': 1
    }

    def __init__(self):
        self.load_cookies()

    async def get_browse(
            self,
            search: str = '',
            where: str = 'everywhere',
            category: str = 'all',
            format: str = 'all',
            year: int = 0,
            when: str = 'always',
            sort: str = 'default',
            sort_order: str = 'decrease',
            page: int = 0,
            request_page: bool = False,
            return_parsed=True,
    ):
        # d - year|w - date|v - format|c - category|t - sort
        # f - sort order|g - where to search

        search = search.replace(
            '.', ''
        ).replace(
            ':', ''
        )

        new_search = ''
        for w in search:

            if 128 < ord(w) < 1039:
                new_search += w.replace(w, f'&#{ord(w)};')

            else:
                new_search += w

        # logger.info(f'{search=}\n{new_search=}')

        quoted_search = MyHttpUtils().quote_plus(new_search)

        url = f'https://{self.host}/browse.php?' \
              f's={quoted_search}&' \
              f'g={self.wheres[where]}&' \
              f'c={self.categories[category]}&' \
              f'v={self.formats[format]}&' \
              f'd={year}&' \
              f'w={self.whens[when]}&' \
              f't={self.sorts[sort]}&' \
              f'f={self.sorts_order[sort_order]}&' \
              f'page={page}'

        logger.info(f'{url=}')
        resp = await self.get(
            url=url
        )
        if return_parsed:
            return await self.parse_browse(
                resp, search, request_page,
            )

        return resp

    async def parse_browse(
            self, resp, search,
            request_page=False,
    ):

        if resp.status != 200:
            return

        soup = BeautifulSoup(resp.content.decode('cp1251'), 'lxml')

        inputed = soup.find('input', {'class': 'w98p'}).get('value')
        if (
                inputed != search
        ) and (
                inputed != f'{search} '
        ) and (
                f'{inputed} ' != search
        ):
            logger.info(f'{search=} != {inputed=}')
            self.items = []
            return

        paginator = soup.find('div', {'class': 'paginator'})
        if paginator:
            lis = paginator.find_all('li')
            pages = int(lis[-2].text)
        else:
            pages = 1

        soup_items = soup.find_all('td', {'class': 'nam'})
        items = []

        for soup_item in soup_items:

            # logger.info(f'{soup_item=}')

            details = soup_item.find('a').get('href')
            id = details.split('=')[1]
            if request_page:
                item = DetailsPage().get_details(id=id)
                items.append(item)
                continue

            item = BrowseItem()
            link = f'http://{self.host}{details}'

            parent = soup_item.parent
            # logger.info(f'{parent=}')

            category = self.gif_categories[parent.find(
                'img', {'alt': ''}
            ).get('src').split('/')[-1]]

            name = soup_item.text
            splitted_name = name.split('/')
            # logger.info(f'{name=}')
            # logger.info(f'{splitted_name=}')
            title = splitted_name[0][0:-1]
            ru_title = title
            en_title = splitted_name[1][1:][0:-1]

            try:
                int(en_title)
                en_title = title
                splitted_name = [splitted_name[0], en_title, *splitted_name[1:]]
            except ValueError:
                pass

            try:
                year = self.kn_find_year(splitted_name)
            except ValueError:
                pass

            translate = splitted_name[3][1:][0:-1]
            try:
                ripped = splitted_name[4][1:]
            except IndexError:
                ripped = None

            seeds = parent.find('td', {'class': 'sl_s'}).text
            peers = parent.find('td', {'class': 'sl_p'}).text

            _locals = locals()
            for key, value in _locals.items():
                if key in BrowseItem.keys:
                    setattr(item, key, value)
                    # logger.info(f'{key}:{value}')

            items.append(item)

        self.items = items
