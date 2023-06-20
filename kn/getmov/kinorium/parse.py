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

from kn.getmov.default import GetMovDefault


class KinoriumParseSite(
    GetMovDefault,
):

    async def kinorium_parse_items(
            self, items, year, file_prefix, skip_write=False,
    ):

        titles = set()

        for item in items:

            # logger.info(f'{item=}')

            href = item.find('a', {'class': 'poster'}).get('href')
            logger.info(f'{href=}')

            _t_ru = item.find(
                'i', {'class': 'movie-title__text'}
            ).text.splitlines()[1]
            _t_ru_word = _t_ru.split()[0]
            _t_ru_index = _t_ru.index(_t_ru_word)

            title_ru = _t_ru[_t_ru_index:]
            try:
                for _year in range(1950, year+2):
                    title_ru = title_ru.replace(
                        ',', ''
                    ).replace(f' {_year}', '').replace(f'{_year}', '')
            except Exception:
                pass

            if title_ru:
                titles.add(title_ru)

            logger.info(f'{title_ru=}')

            info = item.find('div', {'class': 'info'})
            try:
                title_us = info.find('span').string.splitlines()[1]
                title_us = ' '.join(title_us.split())

                for _year in range(1950, year+2):
                    title_us = title_us.replace(
                        ',', ''
                    ).replace(f' {_year}', '')
                        # .replace(f'{_year}', '')

            except:
                title_us = ''

            if title_us and len(title_us) == 4:
                try:
                    int(title_us)
                    title_us = ''
                except ValueError:
                    pass

            if title_us:
                titles.add(title_us)

            logger.info(f'{title_us=}')

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

        if not skip_write:
            self.write_titles(
                to_dir='files/kinorium',
                pre_name=f'{file_prefix}_kinorium',
                titles=titles,
            )
