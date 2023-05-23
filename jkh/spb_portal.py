import re
import hashlib
import asyncio
import os

from datetime import datetime
from collections import namedtuple
from email import utils

from log import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
except ImportError:
    logger.info(f'need install selenium for webdriver and others')

try:
    from bs4 import BeautifulSoup, element
except ImportError:
    logger.info(f'need install beautifulsoup4 for bs4')

from atiny.feed.rss import MyRfeed
from atiny.reos.file.aio import create_dir
from atiny.http import MyHttp


class AbstractSpbPortal:

    async def check_none(self, data, argument=None, func=None):
        if not data:
            return None

        if not argument:
            return data

        if hasattr(data, argument):
            if func:
                return await func(getattr(data, argument))

            return getattr(data, argument)

        return data

    async def del_chars(self, text):
        return "".join(re.findall('[0-9]', text))

    async def strptime(self, text_date, date_format, numbers=True):
        if numbers:
            text_date = ''.join(re.findall('[0-9]|\.', text_date))

        return datetime.strptime(text_date, date_format)

    async def dmY_unix(self, text_date):
        return await self.strptime(text_date, '%d.%m.%Y')

    async def dmy_unix(self, text_date):
        return await self.strptime(text_date, '%d.%m.%y')

    async def dmYHM_unix(self, text_date):
        return await self.strptime(text_date, '%d.%m.%Y, %H:%M', numbers=False)

    def set_keys(self, _locals, keys):
        for key in keys:
            try:
                setattr(self, key, _locals.get(key))
            except:
                logger.info(f'cant set {key=}')


class SpbPortalProblemPagePost(AbstractSpbPortal):

    host_url = 'https://gorod.gov.spb.ru'

    keys: set = set((
        'title', 'author', 'date', 'text', 'files', 'status'
    ))

    title: str
    author: str
    date: datetime
    text: str
    status: str
    files: list

    post_data = {
        'title': 'problem-message__title',
        'message_number': 'message__hiding-number',
        'date': 'problem-message__date',
        'author': 'problem-message__author',
        'text': 'problem-message__text',
        'status': 'sc-dnqmqq cYhETn',

        'download_block': 'label-download-block',
        'file_label': 'file-label',

    }

    def __init__(self, post):
        self.post = post

    async def parse(self, download=''):

        post: element.Tag = self.post
        title = await self.check_none(
            post.find('div', {'class': self.post_data['title']}), 'text',
        )
        date = await self.check_none(
            post.find('div', {'class': self.post_data['date']}), 'text',
            func=self.dmYHM_unix,
        )

        author = await self.check_none(
            post.find('div', {'class': self.post_data['author']}), 'text',
        )
        text = await self.check_none(
            post.find('div', {'class': self.post_data['text']})
        )
        status = await self.check_none(
            post.find('div', {'class': self.post_data['status']}), 'text'
        )
        files_data = await self.check_none(
            post.find_all('div', {'class': self.post_data['file_label']}),
        )
        gallery_data = await self.check_none(
            post.find('ul', {'class': 'gallery'})
        )
        if gallery_data:
            gallery_data = gallery_data.find_all('a')

        logger.info(f'{gallery_data=}')

        files = []
        if not files_data:
            files_data = []
        if not gallery_data:
            gallery_data = []

        skip_urls = set()
        for fl in [*files_data, *gallery_data]:
            fl_data = namedtuple(
                'fl_data',
                (
                    'dwn', 'file_name', 'url', 'path',
                ))

            try:
                find_a = fl.find('a').get('href')
            except:
                find_a = fl.get('href')

            logger.info(f'{fl=}\n{find_a=}')
            url = await self.check_none(
                find_a,
            )
            # url = f'{self.host_url}{url}'
            url = f'{url}'

            if url in skip_urls:
                continue

            skip_urls.add(url)
            file_name = await self.check_none(
                fl.find('a'), 'text'
            )
            if not file_name:
                file_name = url.split('/')[-1]

            if download:
                logger.info(f'{download}/{file_name}')
                if os.path.isfile(
                    f'{download}/{file_name}'
                ):
                    path = f'{download}/{file_name}'
                else:
                    aio_http = await MyHttp(save_cache=True).do(
                        'get', url, tmp_dir=f'{download}/',
                        path=f'{file_name}',
                    )
                    path = aio_http.path
                logger.info(f'{path=}')
            else:
                path = None

            logger.info(f'{url=}, {file_name=}, {path=}')

            files.append(
                fl_data._make(
                    (
                        download, file_name, url, path
                    ))
            )

        logger.info(f'{title=}, {date=}, {author=}, {text=}, {status=}')
        logger.info(f'{files=}')

        self.set_keys(_locals=locals(), keys=self.keys)


class SpbPortalProblem(AbstractSpbPortal):

    page_host_url = f'https://gorod.gov.spb.ru/problems'
    host_url = 'https://gorod.gov.spb.ru'

    page_data = {
        'container': 'new__container',
        'is_correct_container': 'appContent',
        'is_correct_container_next': 'problem-details',
        # list
        'title_reason': 'problem-tile__reason',

        'field_content': 'field__content',
        'sidebar': 'sidebar-group',

        'number': 'problem-details__number',
        'category': 'problem-details__category',
        'reason': 'problem-header__reason',
        'solved_under': 'problem-header__expected-answer',

        'details_list': 'problem-details__list',
        'message_list': 'message-list',

        'tile_image': 'problem-tile__image',
    }

    problem_types = {
        'problem-tile problem-tile_static': 'hidden',
        'problem-tile': 'open'
    }

    problem_status = {
        'problem-tile__status_5': 'answered',
        'problem-tile__status_4': 'mid_answer',
        'problem-tile__status_3': 'queue',
        'problem-tile__status_2': 'mod_wait',
        'problem-tile__status_1': 'created',

    }

    lang_ru = {
        'open': 'Публичная',
        'hidden': 'Частная',
        'answered': 'Получен ответ',
        'mid_answer': 'Промежуточный ответ',
        'queue': 'Рассмотрение',
        'mod_wait': 'Модерация',
        'created': 'Создана',

    }

    keys: set = set((
        'link', 'status', 'type', 'title', 'date', 'id', 'reason',
    ))
    id: int
    link: str
    status: str
    type: str
    title: str
    date: datetime

    # page
    page_keys: set = set((
        'id', 'items', 'category', 'reason', 'solved_under', 'author_name',
        'author_id', 'join',
    ))
    items: list = []
    category: str = ''
    reason: str = ''
    solved_under: int = None
    join: int = 0
    author_name: str = ''
    author_id: int = None

    def __init__(self, soup, def_link, big=False, settings=None):
        self.settings = settings

        tp = None
        for tag in 'a', 'div':
            for pr_type, pr_text in self.problem_types.items():
                _tp = soup.find(tag, {'class': pr_type})
                if _tp:
                    tp = pr_text
                    tp_data = _tp
                    break

        if not tp:
            logger.error(f'no tp: {soup}')
            return

        link = def_link
        status = None
        st_data = None

        for st, st_text in self.problem_status.items():
            _st = soup.find('div', {'class': f'problem-tile__status {st}'})
            if _st:
                status = st_text
                st_data = _st

        if not tp == 'hidden':
            link = f'{self.host_url}{tp_data.get("href")}'

        title = soup.find(
            'div', {'class': 'problem-tile__reason'}).text.replace(
            '\n', '').replace('  ', '')

        _date = soup.find(
            'div', {'class': 'problem-tile__date'}).text.replace(
            ' ', '').replace('\n', '')

        date = datetime.strptime(_date, '%d.%m.%y')
        unix_date = date.strftime('%s')

        _reason = soup.find('div', {'class': self.page_data['title_reason']})
        if _reason:
            reason = _reason.text
        else:
            reason = ''

        tile_image = soup.find('div', {'class': self.page_data['tile_image']}).get('style')

        self.hash_strings = {
            'id': ('unix_date', 'title', 'reason', 'tile_image', 'reason')
        }

        id = self.gen_id('id', locals())

        # logger.info(f'{title=}, {date=}, {id=}')

        self.set_keys(_locals={**locals(), 'type': tp}, keys=self.keys)

        self.html = ''
        self.driver = None
        self.container_found = False

    def gen_id(self, tp, values):
        _strings = []
        for _string in (*self.hash_strings[tp], ):
            try:
                string = str(values[_string])
            except KeyError:
                continue

            _strings.append(string)

        # logger.info(f'{_strings=}')
        hash_object = hashlib.sha256(''.join(_strings).encode('utf8'))
        return hash_object.hexdigest()

    async def get_page(self, url=None, num=None):

        if url:
            page_url = url
        elif num:
            page_url = f'{self.page_host_url}/{num}/'
        elif self.link:
            page_url = self.link
        else:
            page_url = f'{self.page_host_url}/{self.id}'

        logger.info(f'{page_url=}')

        if not num and url:
            num = "".join(re.findall("[0-9]", url))
        elif self.id:
            num = self.id

        if not os.path.isfile(
                f'{self.settings.spb.cache.dir}/{num}.html'
        ):
            cache = False
        else:
            cache = self.settings.spb.cache.use

        if not cache:
            driver = webdriver.Remote(
                command_executor=self.settings.spb.driver_url,
                desired_capabilities=DesiredCapabilities.CHROME,
            )
            driver.set_page_load_timeout(15)
            driver.get(page_url)
            html = driver.page_source
            create_dir(self.settings.spb.cache.dir)
            with open(f'{self.settings.spb.cache.dir}/{num}.html', 'w') as pw:
                pw.write(html)

            self.driver = driver
            self.html = html

            driver.quit()
        else:
            with open(f'{self.settings.spb.cache.dir}/{num}.html', 'r') as pr:
                self.html = pr.read()

    # def __init__(self, url=None, num=None, settings=None):
    async def parse_page(self, url=None, num=None):

        if not self.html:
            await self.get_page()

        soup = BeautifulSoup(self.html, 'lxml')
        containers = soup.find_all('div', {'class': self.page_data['container']})
        for container in containers:
            container: element.Tag
            is_correct_container = container.find(
                'div', id=self.page_data['is_correct_container']
            )
            if is_correct_container:

                is_correct_container = container.find(
                    'div', {'class': self.page_data['is_correct_container_next']}
                )
                if is_correct_container:
                    break
        else:
            for container in containers:
                pass
                # logger.info(f'{container=}\n')
            logger.info(f'cant find correct container')
            return

        self.container_found = True
        # logger.info(f'{container=}')
        sidebar = await self.check_none(
            container.find('div', {'class': self.page_data['sidebar']})
        )
        field_content = await self.check_none(
            sidebar.find_all('div', {'class': self.page_data['field_content']})
        )
        logger.info(f'{sidebar=}\n{field_content=}')
        author_name = None
        author_id = None
        join = 0
        if field_content:
            for field in field_content:
                field: element.Tag
                try:
                    if field.a:
                        author_name = field.text[1:]
                        author_id = field.a.get('href').split('/')[2]
                except:
                    pass

                try:
                    if re.search('человек', field.text):
                        join = int(re.findall('(\d+) ', field.text)[0])
                except:
                    pass

        logger.info(f'{author_name=}, {author_id=} {join=}')

        id = await self.check_none(
            container.find('span', {'class': self.page_data['number']}), 'text',
            func=self.del_chars
        )
        category = await self.check_none(
            container.find('div', {'class': self.page_data['category']}), 'text',
        )
        reason = await self.check_none(
            container.find('div', {'class': self.page_data['reason']}), 'text',
        )
        solved_under = await self.check_none(
            container.find('div', {'class': self.page_data['solved_under']}), 'text',
            func=self.dmY_unix,
        )

        logger.info(f'{category=}, {reason=}, {solved_under=}')

        details_list = container.find('div', {'class': self.page_data['details_list']})
        messages_list = container.find('div', {'class': self.page_data['message_list']})

        items = []
        for message in reversed(list(messages_list)):
            # logger.info(f'{message=}')
            post = SpbPortalProblemPagePost(message)
            await post.parse(
                download=f'{self.settings.spb.files.download_dir}/'
                         f'{id}' if self.settings.spb.files.download else False,
            )
            items.append(post)

        self.set_keys(_locals=locals(), keys=self.page_keys)
        await self.off()

    async def off(self):
        if self.driver:
            self.driver.quit()


class SpbPortalApi32:
    api_version = 'v3.2'
    host_api = f'https://gorod.gov.spb.ru/api/{api_version}'

    statuses = f'{host_api}/statuses'
    classifier = f'{host_api}/classifier'
    districts = f'{host_api}/districts'
    'https://gorod.gov.spb.ru/api/v3.2/problems/by_building//?page=1&count_on_page=1790'


class SpbPortal(AbstractSpbPortal):

    portal_data = {
        'paginator': 'paginator__page'
    }

    keys: set = set((
        'open_problems', 'hidden_problems', 'public_problems', 'answered', 'problems',
        'all_public', 'all_hidden'
    ))
    open_problems: list
    hidden_problems: list
    public_problems: list
    answered: list
    problems: list
    all_public: list
    all_hidden: list

    def __init__(self, mkd_id: int, settings=None):
        self.settings = settings
        self.mkd_id = mkd_id

        self.open_problems = []
        self.hidden_problems = []
        self.public_problems = []
        self.answered = []
        self.problems = []
        self.all_public = []
        self.all_hidden = []

    async def last_problems(self, feeds_dir, per_page=24, page=1):

        # api
        # https://gorod.gov.spb.ru/api/v3.2/problems/by_building//?page=1&count_on_page=1790
        url = f'https://gorod.gov.spb.ru/facilities/{self.mkd_id}/problems/?' \
              f'per_page={per_page}'

        await self.get_problems(per_page=per_page, page=page)

        open_xml = MyRfeed()
        opened_items = []
        for opened in reversed(self.open_problems):
            item = open_xml.create_item(
                title=opened.title, link=opened.link,
                date=utils.format_datetime(opened.unix_date)
            )
            opened_items.append(item)

        open_rss = open_xml.make_feed(
            'НашСПб: Рассмотрение', 'Открытые заявки Наш СПб',
            url,
            opened_items)

        with open(f'{feeds_dir}/spbportal_opened.xml', 'wb') as ow:
            ow.write(open_rss)

        closed_xml = MyRfeed()
        closed_items = []
        for closed in reversed(self.answered):
            item = closed_xml.create_item(
                title=closed.title, link=closed.link,
                date=utils.format_datetime(closed.unix_date)
            )
            closed_items.append(item)

        close_rss = closed_xml.make_feed(
            'НашСПб: Получен ответ', 'Открытые заявки Наш СПб',
            url,
            closed_items
        )

        with open(f'{feeds_dir}/spbportal_answered.xml', 'wb') as ow:
            ow.write(close_rss)

        logger.info(f'end')

    async def get_problems(self, per_page=24, page=1):
        url = f'https://gorod.gov.spb.ru/facilities/{self.mkd_id}/problems/?' \
              f'per_page={per_page}&page={page}'

        try:
            resp = await MyHttp(save_cache=True, load_cache=False).do('get', url)
        except Exception:
            log_stack.error('get mkd')
            return

        soup = BeautifulSoup(resp.content.decode('utf8'), 'lxml')

        _all_problems = soup.find_all('div', {'class': 'problem-tiles__tile'})

        open_problems = [] if not self.open_problems else self.open_problems
        hidden_problems = [] if not self.hidden_problems else self.hidden_problems
        public_problems = [] if not self.public_problems else self.public_problems
        answered = [] if not self.answered else self.answered
        problems = [] if not self.problems else self.problems
        all_hidden = [] if not self.all_hidden else self.all_hidden
        all_public = [] if not self.all_public else self.all_public

        for _problem in _all_problems:
            problem = SpbPortalProblem(_problem, url, settings=self.settings)
            problems.append(problem)

            if problem.type == 'open':
                all_public.append(problem)
            elif problem.type == 'hidden':
                all_hidden.append(problem)

            if problem.status == 'queue':
                open_problems.append(problem)
                if problem.type == 'open':
                    public_problems.append(problem)
                elif problem.type == 'hidden':
                    hidden_problems.append(problem)

            elif problem.status == 'answered':
                answered.append(problem)

        self.set_keys(_locals=locals(), keys=self.keys)

    async def all_problems(self, max_page=None):
        per_page = 48

        url = f'https://gorod.gov.spb.ru/facilities/{self.mkd_id}/problems/?' \
              f'per_page={per_page}&page=1'

        while True:
            try:
                resp = await MyHttp(save_cache=True, load_cache=False).do('get', url)
                break
            except Exception:
                log_stack.error('get mkd')
                await asyncio.sleep(5)

        soup = BeautifulSoup(resp.content.decode('utf8'), 'lxml')
        all_pages = soup.find_all('a', {'class': self.portal_data['paginator']})

        if not max_page:
            try:
                max_page = int(re.findall('(\d+)', all_pages[-2].text)[0])
            except:
                max_page = len(all_pages)

        for pg_num in range(1, max_page+1):
            logger.info(f'{pg_num=}')
            await self.get_problems(per_page=48, page=pg_num)
            logger.info(f'{len(self.all_public)}')
            logger.info(f'{len(self.problems)}')

    async def test(self):

        allpg = await self.all_problems()
        l = 16
        for problem in self.all_public:

            await problem.parse_page(url=problem.link)

        return
        # page = SpbPortalProblemPage(
        #     num=1,
        #     settings=self.settings
        # )
        # await page.parse_page()
