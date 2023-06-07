import re
import os
import asyncio

from bs4 import BeautifulSoup, Tag

from config import settings
from atiny.http.utils import MyHttpUtils
from log import logger

from .extra import DetailsExtra
from ..find_vars import KinozalVarsFinder


class DetailsPage(
    DetailsExtra, KinozalVarsFinder,
):

    keys = [
        'link', 'name', 'imdb',
        'title', 'en_title', 'ru_title', 'year', 'image', 'translate', 'ripped',
        'seeds', 'peers', 'who_full', 'info_hash', 'files',
        'roles_data', 'about',
        'specs', 'release',  'screens',
    ]

    imdb: str = None
    link: str
    name: str
    title: str
    en_title: str
    ru_title: str
    year: int
    image: str = None
    translate: str
    ripped: str
    seeds: int
    peers: int
    who_full: list
    info_hash: str
    files: str
    roles_data: dict = {'text': '', 'links': []}
    about: str
    specs: str
    release: str
    screens: list

    def __init__(self, id: int = None):
        self.id = id

    async def get_details(self, id: int = None, return_parsed=True):
        if id:
            self.id = id

        if not self.id:
            return

        while True:
            resp = await self.get(
                f'https://{self.host}/details.php?id={self.id}',
            )
            if not resp.error and resp.status == 200:
                break

            logger.info(f'{resp.status=} wait')
            await asyncio.sleep(10)

        if return_parsed:
            return await self.parse_details(resp)

        return resp

    async def parse_details(self, resp):

        if resp.status != 200:
            return

        link = f'http://{self.host}/details.php?id={self.id}'
        logger.info(f'{link=}')

        soup = BeautifulSoup(resp.content.decode('cp1251'), 'lxml')

        try:
            imdb = soup.find(text='IMDb').parent.get('href').split('/')[-2]
        except Exception:
            pass

        title = soup.find('meta', {'property': 'og:title'}).get('content')
        name = title
        splitted_name = title.split('/')
        ru_title = ''.join(splitted_name[0][0:-1])
        en_title = ''.join(splitted_name[1][1:-1])

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

        translate = ''.join(splitted_name[3][1:-1])
        ripped = ''.join(splitted_name[4][1:])

        image = soup.find('meta', {'property': 'og:image'}).get('content')

        li_class_tp = soup.find('li', {'class': 'tp'}, string='Участники').parent
        lis = li_class_tp.find_all('li')
        li_data = {
            'seed': {'text': 'Раздают', 'n': 0, 'torm': None},
            'peers': {'text': 'Скачивают', 'n': 0, 'torm': None},
            'files': {'text': 'Список файлов', 'n': 0, 'torm': None},
            'image': {'text': title, 'n': None, 'src': None},
            'full': {'text': 'Скачали', 'n': None, 'torm': None}
        }
        for li in lis:
            li: Tag

            src = None
            href = None
            onclick = None

            a = li.find('a')
            if not a:
                continue

            href = a.get('href')

            a_title = a.get('title')
            img = li.find('img')
            if img:
                src = img.get('src')

            if href:
                onclick = a.get('onclick')

            for key, values in li_data.items():
                if onclick and 'torm' in values and values['text'] in onclick:
                    li_data[key]['torm'] = onclick.split(',')[1]
                    li_data[key]['n'] = int(
                        ''.join(
                            re.findall('\d+', onclick.split(',')[2])
                        )
                    )

                if a_title and img and src and 'src' in values:
                    li_data[key]['src'] = src

        seeds = li_data['seed']['n']
        peers = li_data['peers']['n']
        full = li_data['full']['n']

        who_full = (
            await self.get_action(li_data['full']['torm'])
        ).content.decode('utf8')
        who_full, n = who_full.split('|'), 6
        who_full = [x[1] for x in [who_full[idx:idx+n] for idx in range(0, len(who_full), n)][0:-1]]

        files = await self.get_action(li_data['files']['torm'])
        _soup = BeautifulSoup(
            files.content.decode("utf8"),
            'lxml'
        )
        # logger.info(f'1{_soup=}')
        files = _soup.find_all('li')
        # logger.info(f'2{files=}')
        info_hash = files[0].text.replace('Инфо хеш: ', '')
        files = '\n'.join([x.text for x in files])

        image = li_data['image']['src']

        mn1_content = soup.find('div', {'class': 'mn1_content'})
        specs_key = mn1_content.find(
            'a', {'href': '#'}, string='Техданные'
        ).get('onclick').split(f'{self.id},')[1].split(')')[0]
        release_key = mn1_content.find(
            'a', {'href': '#'}, string='Релиз'
        )
        if release_key:
            release_key = release_key.get(
                'onclick'
            ).split(f'{self.id},')[1].split(')')[0]
        screens_key = mn1_content.find(
            'a', {'href': '#'}, string='Скриншоты'
        )
        if screens_key:
            screens_key = screens_key.get(
                'onclick'
            ).split(f'{self.id},')[1].split(')')[0]

        justify_search = mn1_content.find_all('div', {'class': 'bx1 justify'})

        for info in justify_search:
            # logger.info(f'{info=}')
            try:
                roles_text = info.text[info.text.index('В ролях: ')+9:]
            except ValueError:
                continue

            try:
                author_text = info.text[info.text.index('Режиссер: ')+10:]
            except ValueError:
                author_text = '\n'

            roles_data = {
                'text': info.text,
                'links': {}
            }

            for _name in (
                    *roles_text.splitlines()[0].split(','),
                    *author_text.splitlines()[0].split(','),
            ):

                if not _name:
                    continue

                if _name[0] == ' ':
                    _name = ''.join(_name[1:])

                if _name[-1] == ' ':
                    _name = ''.join(_name[:-2])

                _link = f'https://{self.host}/persons.php?' \
                        f's={MyHttpUtils().quote(_name)}'
                roles_data['links'][name] = _link

            break

        for info in justify_search:
            logger.info(f'{info=}')
            try:
                info.text.index('О фильме')
            except ValueError:
                continue

            about = info.text

        if screens_key:
            screens = await self.get_showtab(screens_key)
            screens = re.findall(
                '<a href="(.*?)"', screens.content.decode('cp1251')
            )
        else:
            screens = []

        if release_key:
            release = await self.get_showtab(release_key)
            _soup = BeautifulSoup(
                f'<html>{release.content.decode("utf8")}</html>',
                'lxml'
            )
            release = _soup.text
        else:
            release = ''

        specs = soup.find('div', {'class': 'justify mn2 pad5x5'}).text

        # if specs_key:
        #     specs = await self.get_showtab(specs_key)
        #     _soup = BeautifulSoup(
        #         f'<html>{specs.content.decode("utf8")}</html>',
        #         'lxml'
        #     )
        #     specs = _soup.text
        # else:
        #     specs = ''

        _locals = locals()

        for key, value in _locals.items():
            if key in self.keys:
                setattr(self, key, value)
                logger.info(f'{key}:{value}')

        return True
