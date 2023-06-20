try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger
except ImportError:
    from atiny.log import logger

from config import secrets

from bs4 import BeautifulSoup

from atiny.http import MyHttp
from atiny.http.utils import MyHttpUtils

from kn.getmov.default import GetMovDefault

from .parse import KinoriumParseSite


class KinoriumDefaultSite(
    KinoriumParseSite
):

    kinoriuim_order = {'sort_date', 'rating', }
    kinorium_countries = {
        'ru': 165,
    }
    kinorium_lang: str
    kinorium_host: str
    max_page: int

    kinorium_token_key: str
    kinorium_token_value: str
    kinorium_secret: str
    kinorium_phpsessid: str
    kinorium_session: str

    def kinorium_config(self, lang='ru'):
        self.kinorium_lang = lang
        self.kinorium_host = f'{lang}.kinorium.com'

    async def kinorium_auth(self):
        self.kinorium_token_key = secrets.kinorium.token_key
        self.kinorium_token_value = secrets.kinorium.token_value
        self.kinorium_secret = secrets.kinorium.secret
        self.kinorium_phpsessid = secrets.kinorium.phpsessid
        self.kinorium_session = secrets.kinorium.session

        return
        if (
                self.kinorium_token_key
        ) and (
                self.kinorium_token_value
        ) and (
                self.kinorium_secret
        ):
            return

        http = MyHttp()

        resp = await http.get(
            f'https://{self.kinorium_host}/R2D2',
        )

    async def kinorium_headers(self):

        headers = {
            'authority': self.kinorium_host,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cookie': '',
            'referer': '',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
            'x-requested-with': 'XMLHttpRequest',
            f'x-token-{self.kinorium_token_key}': self.kinorium_token_value,
            'x-token-secret': self.kinorium_secret,
        }

        return headers

    async def kinorium_type_request(
            self,
            page, per_page, year,
            order,
            exclude_countries=['ru', ],
            list_only='',
            type='R2D2',
            r_type='',
    ):

        per_page = 50

        if type == 'R2D2':
            search_title = 'Поиск лучших фильмов: 2022 год'
        else:
            search_title = 'sorry for sometime using this, ' \
                           'but as You say API is for big project only'

        if type == 'R2D2' or type == 'home':
            _exclude_countries = ','.join(
                [f'{self.kinorium_countries[x]}' for x in exclude_countries]
            )
            search_settings = MyHttpUtils().quote(
                f'order={order}&'
                f'page={page}&'
                f'perpage={per_page}&'
                f'exclude_countries[]{_exclude_countries}&'
                f'years_min={year}&'
                f'years_max={year}'
            )

            url_settings = f'order={order}&' \
                           f'page={page}&' \
                           f'perpage={per_page}&' \
                           f'exclude_countries' \
                           f'{MyHttpUtils().quote(f"[]")}={_exclude_countries}&' \
                           f'years_min={year}&' \
                           f'years_max={year}'

            url = f'https://{self.kinorium_host}/handlers/filmList/?' \
                  f'type={type}&' \
                  f'{url_settings}&' \
                  f'list_only={list_only}&' \
                  f'title={MyHttpUtils().quote(search_title, colon=True)}'

        if type == 'online' or type == 'premier':
            search_settings = MyHttpUtils().quote(
                f'order={order}&'
                f'page={page}&'
                f'perpage={per_page}&'
                f'show_viewed=1&'
                f'show_status=0&'
                f'years_min=&'
                f'years_max=&'
                f'pids=&'
            )

            url_settings = f'order={order}&' \
                           f'page={page}&' \
                           f'perpage={per_page}&' \
                           f'show_viewed=1&' \
                           f'show_status=0&' \
                           f'years_min=&' \
                           f'years_max=&' \
                           f'pids=&'

            url = f'https://{self.kinorium_host}/handlers/filmList/?' \
                  f'type={type}&' \
                  f'r_type={r_type}&' \
                  f'{url_settings}&' \
                  f'title={MyHttpUtils().quote(search_title, colon=True)}'

        # proxy = 'http://192.168.55.59:8880'

        http = MyHttp(
            proxy=self.proxy,
            save_cache=True,
            save_headers=True,
            # load_cache=True,
        )

        headers = await self.kinorium_headers()
        headers['referer'] = f'https://{self.kinorium_host}/{type}/?{url_settings}'

        headers['cookie'] = f'PHPSESSID={self.kinorium_phpsessid}; ' \
                            f'session={self.kinorium_session}; ' \
                            'hiddenTooltips=%5B%5D; ' \
                            'pixr=1; broTheme=; ' \
                            'cinema_guide=; ' \
                            'time_shift=0; ' \
                            'autoTheme=1; brbr=3; '

        if type == 'R2D2' or type == 'home':
            headers['cookie'] += f'search_settings={search_settings}; ' \
                                 f'guide={type.lower()}'

        logger.info(f'{url=}')

        resp = await http.get(
            url=url,
            headers=headers,
        )

        return resp
