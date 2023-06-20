import re
import os
import asyncio

from bs4 import BeautifulSoup, Tag

from config import settings
from atiny.http.utils import MyHttpUtils
from log import logger, log_stack

# from .extra import DetailsExtra
from ..find_vars import TgxVarsFinder
from ..http import Http


class TgxDetailsPage(
    Http,
    TgxVarsFinder,
):

    keys = [
        'id',
        'link',
        'name',
        'title',
        'year',
        'info_hash',
        'imdb',
        'image',
        'description',
        'magnet',

    ]

    id: int
    link: str
    name: str
    title: str = None
    year: int
    info_hash: str
    imdb: str = None
    image: str
    description: str = ''
    magnet: str

    def __init__(self, id: int = None, pre_item=None):
        self.id = id
        self.pre_item = pre_item

    async def get_details(self, id: int = None, return_parsed=True):
        if id:
            self.id = id

        if not self.id:
            return

        while True:
            url = f'https://{self.host}/torrents-details.php?id={self.id}'
            resp = await self.get(
                url=url
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

        # with open('resp.html', 'wb') as wb:
        #     wb.write(resp.content)

        link = f'https://{self.host}/torrents-details.php?id={self.id}'

        soup = BeautifulSoup(resp.content.decode('latin-1'), 'lxml')

        info_table = soup.find('div', {'class': 'torrentpagetable txlight'})
        try:
            imdb = soup.find('a', {'id': 'imdbpage'}).get('href').split('/')[-1]
        except Exception:
            try:
                imdb = 'tt' + re.findall(
                    'https://www.imdb.com/title/tt(.*?24072236)', soup.text
                )[0]
            except Exception:
                log_stack.error(f'imdb1')
            log_stack.error(f'imdb2')

        magnet = info_table.find('a', {'class': 'btn btn-danger lift txlight'}).get('href')

        _description = soup.find(
            'a', {'name': 'description'}
        ).parent.text.replace(
            'Need anything from us?\nDrop your request @\n Perma forum linkGalaxyRG + GalaxyTV \xa0request thread > post #202403 ', ''
        )
        description_index = _description.index('Description\n')
        description = ''.join(_description[description_index:])

        table = soup.find('div', {'class': 'torrentpagetable limitwidth txlight'})
        _info_hash = table.find(
            'div', string='Info Hash:',
        )
        info_hash = _info_hash.parent.find('span', 'linebreakup').text

        if self.pre_item:
            self.set_locals(self.pre_item)
            self.set_locals(locals())
            return True

        self.set_locals(locals())

        return True
