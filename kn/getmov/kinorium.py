try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger
except ImportError:
    from atiny.log import logger

from bs4 import BeautifulSoup

from atiny.http import MyHttp
from atiny.http.utils import MyHttpUtils

from .default import GetMovDefault


class KinoriumSite(
    GetMovDefault,
):

    kinoriuim_order = {'sort_date', 'rating', }
    kinorium_countries = {
        'ru': 165,
    }
    kinorium_host = 'ru.kinorium.com'

    kinorium_token_key: str
    kinorium_token_value: str
    kinorium_secret: str

    async def kinorium_auth(self):
        self.kinorium_token_key = f'' \
                                  f'3f5ef03187d8c8735d4bd0d08ad30e96'

        self.kinorium_token_value = f'' \
                                    f'8e885054c65a64a51ecc262d9b0f0a67'
        self.kinorium_secret = f'' \
                               f'6175d40124b7187b8389b0cd66dd0fec'

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

    async def kinorium_filelist_request(
            self, page, per_page, order, exclude_countries,
            year, list_only,
    ):

        type = 'R2D2'
        search_title = 'Поиск лучших фильмов: 2022 год'

        _exclude_countries = ','.join(
            [f'{self.kinorium_countries[x]}' for x in exclude_countries]
        )

        proxy = 'http://192.168.55.59:8880'

        http = MyHttp(
            proxy=proxy,
            save_cache=True,
            save_headers=True,
            # load_cache=True,
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

        headers = {
            'authority': self.kinorium_host,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cookie': 'PHPSESSID=l08tg7kfbt3hugfgcv7t43aom4; '
                      'session=tpqq877pvg26e9dfgas2mvcnib; '
                      'hiddenTooltips=%5B%5D; '
                      'pixr=1; broTheme=; '
                      'cinema_guide=; '
                      'time_shift=0; '
                      'autoTheme=1; brbr=3; '
                      f'search_settings={search_settings}; '
                      f'guide={type.lower()} ',
            'referer': f'https://{self.kinorium_host}/{type}/?{url_settings}',
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

        resp = await http.get(
            url=url,
            headers=headers,
        )

        return resp

    async def kinorium_filmlist(
            self, order='-year', exclude_countries=('ru', ),
            year=2022, list_only=1,
            max_page=None,
    ):

        await self.kinorium_auth()

        per_page = 200

        resp = await self.kinorium_filelist_request(
            page=1, per_page=per_page, order=order,
            exclude_countries=exclude_countries, year=year,
            list_only=list_only,
        )

        if resp.error or resp.status != 200:
            logger.info(f'{resp.status=}')
            return

        js = json.loads(resp.content.decode('utf8'))

        result = js.get('result')
        count = int(result.get('count'))
        resp_max_page = round(count / per_page)

        if not max_page:
            max_page = resp_max_page

        logger.info(f'{max_page=}')

        i = 0
        items = []
        for page in range(1, max_page+1):

            result = js.get('result')
            html = result.get('html')

            js = json.loads(resp.content.decode('utf8'))

            soup = BeautifulSoup(html, 'html.parser')
            items.extend(soup.find_all('div', {'class': 'filmList__item-content'}))

            if page == 1:
                continue

            resp = await self.kinorium_filelist_request(
                page=page, per_page=per_page, order=order,
                exclude_countries=exclude_countries, year=year,
                list_only=list_only,
            )

            if resp.error or resp.status != 200:
                logger.info(f'{resp.status=}')
                return

            i += 1

            # if i == 3:
            #     break

        titles = set()

        for item in items:

            href = item.find('a', {'class': 'poster'}).get('href')
            logger.info(f'{href=}')

            _t_ru = item.find(
                'i', {'class': 'movie-title__text'}
            ).text.splitlines()[1]
            _t_ru_word = _t_ru.split()[0]
            _t_ru_index = _t_ru.index(_t_ru_word)

            title_ru = _t_ru[_t_ru_index:]
            if title_ru:
                titles.add(title_ru)

            logger.info(f'{title_ru=}')

            info = item.find('div', {'class': 'info'})
            title_us = info.find('span').string.splitlines()[1]
            title_us = title_us.replace(
                ',', ''
            ).replace(f'{year}', '')
            title_us = ' '.join(title_us.split())
            if title_us:
                logger.info(f'{title_us=}')
                titles.add(title_us)
            else:
                logger.info(f'no us title')

            movie_name = item.find(
                'div', {'class': 'statusWidgetData'}
            ).get('data-moviename')

            if movie_name:
                titles.add(movie_name)

            logger.info(f'{movie_name=}')

        titles = set(
            [
                self.clear_title(x) for x in titles
            ]
        )

        self.write_titles(
            to_dir='files/kinorium',
            pre_name=f'{year}_kinorium',
            titles=titles,
        )
