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

from .default import KinoriumDefaultSite


class KinoriumFilmListSite(
    KinoriumDefaultSite,
):

    async def kinorium_filmlist(
            self, order='-year', exclude_countries=('ru', ),
            year=2022, list_only=1,
            max_page=None, skip_write=False,
    ):

        await self.kinorium_auth()

        per_page = 200

        resp = await self.kinorium_type_request(
            page=1, per_page=per_page, order=order,
            exclude_countries=exclude_countries, year=year,
            list_only=list_only,
        )

        if resp.error or resp.status != 200:
            logger.info(f'{resp.status=}')
            return []

        self.write_resp_content(resp)

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

            resp = await self.kinorium_type_request(
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

        await self.kinorium_parse_items(
            items=items, file_prefix=f'{year}_{self.kinorium_lang}',
            skip_write=skip_write,
            year=year,
        )