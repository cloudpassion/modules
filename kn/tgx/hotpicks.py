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

from ..tgx.details import TgxDetailsPage

from .default import TgxDefault
from .find_vars import TgxVarsFinder


class TgxHotPicksItem(TgxVarsFinder):

    keys = ['id', 'link', 'name', 'image', 'title', 'year']
    id: int
    link: str
    name: str
    image: str

    title: str = None
    year: int


class TGxHotPicks(
    TgxDefault
):

    items: list = []
    keys = ['items', ]

    async def tgx_request(self, url):

        http = MyHttp(
            proxy=self.proxy,
            save_cache=True,
            save_headers=True,
            # load_cache=True,
        )

        logger.info(f'{url=}')

        resp = await http.get(
            url=url,
        )

        return resp

    async def tgx_get_hot_picks(self, cat):

        url = f'https://{self.tgx_host}/torrents-hotpicks.php?cat={cat}'
        logger.info(f'{url=}')

        resp = await self.tgx_request(
            url=url
        )

        if resp.error or resp.status != 200:
            logger.info(f'{resp.status=}')
            return []

        # with open('resp.html', 'wb') as wb:
        #     wb.write(resp.content)

        soup = BeautifulSoup(resp.content.decode('latin-1'), 'lxml')
        soup_items = soup.find_all('div', {'class': 'hotpicks'})

        items = []
        for soup_item in soup_items:
            # logger.info(f'{soup_item=}')

            item = TgxHotPicksItem()

            href = soup_item.find('a').get('href')
            link = f'https://{self.tgx_host}/{href}'
            
            try:
                id = int(href.split('id=')[-1])
            except Exception as exc:
                logger.info(f'{exc=}')
                id = int(href.split('id=')[-1].split('&')[0])

            name = soup_item.find('img').get('alt')

            image = soup_item.find('img').get('data-src')

            splitted_name = name.split('.')
            # logger.info(f'{splitted_name=}')

            if cat != 3:
                year = item.tgx_find_year(splitted_name)
                year_index = splitted_name.index(f'{year}')

                title = ' '.join(splitted_name[0:year_index])

            item.set_locals(locals())

            items.append(item)

        self.items = items
        return items

