import re
import os
import asyncio

from bs4 import BeautifulSoup, Tag
from collections import defaultdict

from config import settings
from atiny.http.utils import MyHttpUtils
from log import logger

from ..http import Http
from ..details import DetailsPage
from ..find_vars import KinozalVarsFinder


class TopItem(
    KinozalVarsFinder,
):

    keys = [
        'id', 'name', 'link',
        'title', 'en_title', 'ru_title', 'year', 'translate', 'ripped',
    ]

    id: int
    name: str
    link: str
    title: str
    en_title: str
    ru_title: str
    year: int
    translate: str
    ripped: str
    poster: str


class TopPage(
    Http,
    KinozalVarsFinder,
):

    keys = [
        'items', 'page', 'pages'
    ]

    items: list = []
    pages: int = 0

    genres = defaultdict(
        lambda: '',
        {}
    )

    categories = {
        'shares': 0,
        'films': 1,
        'serials': 3,
        'cartoons': 2,
    }

    release_years = {
        'all': 0,
        **{k: 12 for k in range(2021, 2023+1)},
        **{k: 11 for k in range(2018, 2020+1)},
        **{k: 10 for k in range(2015, 2017+1)},
        **{k: 1 for k in range(2012, 2014+1)},
        **{k: 2 for k in range(2009, 2011+1)},
        **{k: 3 for k in range(2006, 2008+1)},
        **{k: 4 for k in range(2001, 2005+1)},
        **{k: 5 for k in range(1996, 2000+1)},
        **{k: 6 for k in range(1992, 1995+1)},
        **{k: 7 for k in range(1982, 1991+1)},
        **{k: 8 for k in range(1972, 1981+1)},
        **{k: 9 for k in range(1951, 1971+1)},
        '2021-2023': 12,
        '2018-2020': 11,
        '2015-2017': 10,
        '2012-2014': 1,
        '2009-2011': 2,
        '2006-2008': 3,
        '2001-2005': 4,
        '1996-2000': 5,
        '1992-1995': 6,
        '1982-1991': 7,
        '1972-1981': 8,
        '1951-1971': 9
    }

    countries = {
        'all': 0,
    }

    formats = {
        'all': 0,
        'hd': 2,
    }

    uploaded = {
        'all': 0,
        'week': 1,
        'month': 2,
        'three_month': 3,
        'half_year': 6,
    }

    sort = {
        'seeds': 0,
        'peers': 1,
        'comments': 2,
    }

    def __init__(self):
        self.load_cookies()

    async def get_top(
            self,
            genre: str = '',
            category: str = 'shares',
            release_years: str = 'all',
            country: str = 'all',
            format: str = 'all',
            uploaded: str = 'all',
            sort: str = 'seeds',
            page: int = 0,
            request_page: bool = False,
            return_parsed=True,
    ):

        # j - genre, t - category,
        # d - years, f - format, k - country
        # w - uploaded, s - sort

        url = f'https://{self.host}/top.php?' \
              f'j={self.genres[genre]}&' \
              f't={self.categories[category]}&' \
              f'd={self.release_years[release_years]}&' \
              f'k={self.countries[country]}&' \
              f'f={self.formats[format]}&' \
              f'w={self.uploaded[uploaded]}&' \
              f's={self.sort[sort]}&' \
              f'page={page}'

        logger.info(f'{url=}')
        resp = await self.get(
            url=url
        )
        if return_parsed:
            return await self.parse_top(
                resp, request_page,
            )

        return resp

    async def parse_top(
            self, resp,
            request_page=False,
    ):

        if resp.status != 200:
            return

        soup = BeautifulSoup(resp.content.decode('p1251'), 'lxml')

        paginator = soup.find('div', {'class': 'paginator'})
        if paginator:
            lis = paginator.find_all('li')
            pages = int(lis[-2].text)
        else:
            pages = 1

        try:
            current = paginator.find('li', {'class': 'current'})
        except AttributeError:
            logger.info(f'no items')
            self.items = []
            self.pages = 0
            return

        page = int(current.text)

        bx = soup.find('div', {'class': 'bx1 stable'})
        # logger.info(f'{bx=}')

        soup_items = bx.find_all('a')

        items = []

        for soup_item in soup_items:

            # logger.info(f'{soup_item=}')

            details = soup_item.get('href')
            id = details.split('=')[1]
            if request_page:
                item = DetailsPage().get_details(id=id)
                items.append(item)
                continue

            item = TopItem()

            name = soup_item.get('title')
            splitted_name = name.split('/')

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

            poster = soup_item.find('img').get('src')
            if poster and 'http' not in poster:
                poster = f'https://{self.host}{poster}'

            _locals = locals()
            for key, value in _locals.items():
                if key in TopItem.keys:
                    setattr(item, key, value)
                    # logger.info(f'{key}:{value}')

            items.append(item)

        _locals = locals()
        for key, value in _locals.items():
            if key in self.keys:
                setattr(self, key, value)
