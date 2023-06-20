import re
import time

try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger, log_stack
except ImportError:
    from atiny.log import logger, log_stack

from bs4 import BeautifulSoup

from atiny.http import MyRequestsHTTP

from .default import GetMovDefault


class IMDBSite(
    GetMovDefault,
):

    async def imdb_upcoming_list(self):

        titles = set()
        entries = []
        for region in ['US', 'RU', 'UA', ]:
            for tp in ['MOVIE', 'TV', ]:
                link = f'https://www.imdb.com/calendar/?' \
                       f'ref_=rlm&' \
                       f'region={region}&' \
                       f'type={tp}'

                http = MyRequestsHTTP()
                resp = http.get(
                    link,
                    headers={
                        'User-Agent': self.user_agent,
                    }
                )

                #with open('get_temp.html', 'wb') as hw:
                #    hw.write(resp.content)

                text = resp.content.decode('utf8')

                soup = BeautifulSoup(text, 'lxml')

                main = soup.find('script', {'id': '__NEXT_DATA__'})
                groups = json.loads(main.text).get('props').get('pageProps').get('groups')

                for group in groups:
                    for entry in group.get('entries'):
                        entries.append(entry)

        for entry in entries:
            title = entry.get('titleText')
            titles.add(title)

        self.write_titles(
            to_dir='files/imdb/',
            pre_name=f'{time.strftime("%Y")}_imdb_upcoming',
            titles=titles
        )

    async def imdb_year_list(self, year=2022):

        titles = set()
        link = f'https://www.imdb.com/search/title/?' \
               f'title_type=feature&' \
               f'release_date={year}-01-01,{year}-12-31&view=simple'

        _next = 0

        http = MyRequestsHTTP()
        resp = http.get(f'{link}&start={_next}&ref_=adv_nxt')

        # with open('get_temp.html', 'wb') as hw:
        #     hw.write(resp.content)

        text = resp.content.decode('utf8')
        soup = BeautifulSoup(text, 'lxml')

        _count = soup.find('div', {'class': 'desc'})
        count = int(
            ''.join(
                re.findall('[0-9]', re.findall(' (.*?) titles', f'{_count}')[0])
            )
        )

        for page in range(0, int(count/50)):
            print(f'{page=}')
            try:
                main = soup.findAll('a') #, 'href') #v', {'class': 'lister list detail sub-list'})

                text = ''
                for a in main:
                    text += f'{a}\n'

                _titles = re.findall('<a href="/title/.*/">(.*?)</a>', text)

                for title in _titles:
                    titles.add(title)

                _next += 50

                resp = http.get(f'{link}&start={_next}&ref_=adv_nxt')
                text = resp.content.decode('utf8')
                soup = BeautifulSoup(text, 'lxml')

                # with open('get_temp.html', 'wb') as hw:
                #     hw.write(resp.content)

            except Exception as exc:
                log_stack.error('check')

            time.sleep(2)

        self.write_titles(
            to_dir='files/imdb/',
            pre_name=f'{time.strftime("%Y")}_imdb_year',
            titles=titles
        )
