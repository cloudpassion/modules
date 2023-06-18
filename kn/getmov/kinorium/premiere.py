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

from .default import KinoriumDefaultSite


class KinoriumPremierSite(
    KinoriumDefaultSite
):
    #https://en.kinorium.com/movies/premier/online/?order=premier_date'
    #https://en.kinorium.com/movies/premier/?order=premier_date
    #https://en.kinorium.com/movies/online/
    #https://en.kinorium.com/movies/cinema/

    async def kinorium_get_movies_upcoming(
            self, year, max_page=None, skip_write=False,
            tp=['premier', 'online', 'home'],
    ):
        items = []

        for where in tp:
            _items = await self.kinorium_movies_premier(
                year=year,
                type=where,
                max_page=max_page,
                skip_parse=True,
            )

            logger.info(f'{where=}, {len(items)}')
            items.extend(_items)

        if not items:
            return

        await self.kinorium_parse_items(
            year=year,
            items=items,
            file_prefix=f'{year}_{self.kinorium_lang}_upcoming',
            skip_write=skip_write,
        )

    async def kinorium_movies_premier(
            self,
            year,
            type='premier',
            order='-premier_date',
            max_page=None,
            per_page=50,
            skip_write=False,
            skip_parse=False
    ):

        await self.kinorium_auth()

        resp = await self.kinorium_type_request(
            type=type,
            page=1, per_page=per_page, order=order,
            year='',
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
                type=type,
                page=page, per_page=per_page, order=order,
                year=year,
            )

            if resp.error or resp.status != 200:
                logger.info(f'{resp.status=}')
                return

            i += 1

            # if i == 3:
            #     break

        if not skip_parse:
            await self.kinorium_parse_items(
                items=items,
                year=year,
                file_prefix=f'{year}_{self.kinorium_lang}',
                skip_write=skip_write,
            )

        return items
