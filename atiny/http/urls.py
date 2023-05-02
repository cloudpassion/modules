import re
import asyncio


try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback


from .aiohttp import MyHttp
from .requests import MyRequestsHTTP


class MyUrls:

    where = ('reddit', 'imgur.com', )

    def __init__(self, data=None, where=False, what=None, proxy=None):
        self.data = data
        self.url = None
        self.links = None
        self.what = what
        self.where = where
        self.recompile = \
            ('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', )
        self.skip_urls = set()
        self.aio_http = False
        self.req_http = False

        if self.what:
            self.aio_http = MyHttp(proxy=proxy)
            self.req_http = MyRequestsHTTP(proxy=proxy)

        #self.conf = MyConfig()
        #self.conf.init(f'{"/".join(str(Path(__file__)).split("/")[:-1])}/.def.ni')

    async def check(self):
        if not self.where:
            return await self.find_urls()
        else:
            if self.where == 'reddit':
                self.recompile = (r'<span><a href="(.*?)">\[link\]</a>',
                                  'src="(.*?)(?: |")')
            else: pass

    async def tiny(self, _url):
        await asyncio.sleep(0)
        return _url

    def get_domain(self, url):
        return url.split('/')[2::1]

    async def check_domain(self, _url):

        if not self.what:
            return [True, _url]

        elif self.what == 'media':

            if not _url:
                return [False, _url]

            url_domain = _url.split('/')[2:3]
            if not url_domain:
                logger.debug(f'domain check: {_url}')
                return [False, False]

            if _url.split('?')[0] in self.skip_urls:
                return [False, False]

            self.skip_urls.add(_url.split('?')[0])

            try:
                if 'imgur.com' in url_domain[0] and not 'i.imgur.com' in url_domain[0]:
                    if 'jpg' in _url or 'png' in _url or 'jpeg' in _url or 'bmp' in _url:
                        return [True, _url]
                    return [False, _url, '<link rel="image_src".*?href="(.*?)"']

                elif re.search('deviantart.com', url_domain[0]):
                    return [False, _url, 'data-super-full-img="(.*?)"']

                elif re.search('flickr.com', url_domain[0]):
                    return [False, _url, '<meta property="og:image" content="(.*?)"']

                elif re.search('www.reddit.com', url_domain[0]):
                    #return get_img(re.findall(
                    # '<meta name="description" content="(htt[p|ps]:.*?[\.jpg|\.png|\.jpeg|\.bmp]) ', r.text))[0]
                    logger.debug(f'check_wwwredditcom: {_url}')
                    return [False, False]

                elif re.search('asciinema.org', url_domain[0]):
                    return [False, _url, r'<meta property="og:image" content="(.*?)"']

                elif re.search('upload.wikimedia.org', url_domain[0]):
                    try:
                        _wiki = _url+'/1024px-'+_url.split('/')[-1]
                    except:
                        _wiki = _url
                        log_stack.info(f'FIX_WIKI_IMG: {_url}')
                    return [True, _wiki]

                elif re.search('youtube.com', url_domain[0]) or re.search('youtu.be', url_domain[0]) or re.search('www.youtube.com', url_domain[0]) or re.search('www.youtu.be', url_domain[0]):
                    try: _ytb_t = _url.split('v%3D')[1].split('%')[0]
                    except:
                        try: _ytb_t = _url.split('v=')[1].split('&')[0]
                        except:
                            try: _ytb_t = _url.split('v=')[1]
                            except:
                                try: _ytb_t = _url.split('/')[-1]
                                except:
                                    log_stack.info(f'FIXYTB_RETURN_FALSE: {_url}')
                                    return [False, False]

                    try: _ytb_t = _ytb_t.split('?')[0]
                    except: log_stack.info('FIX:YTB_QUESTION')

                    resp = await self.aio_http.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet' \
                                                   +'&fields=items(id%2Ckind%2Csnippet)' \
                                                   +'&key={self.conf.get("api", "yt_api")}&id={_ytb_t}')
                    if resp.error:
                        return [False, False]
                    data = json.loads(resp.content.decode('utf8'))
                    _ytb = False
                    for resol in 'maxres', 'standard', 'high':
                        try:
                            _ytb = data.get('items')[0].get('snippet').get('thumbnails').get(resol).get('url')
                        except:
                            continue
                        if not _ytb == None:
                            break
                    return [_ytb, _ytb]

                elif re.search('gfycat.com', url_domain[0]):

                    if 'detail' in _url: _gfy = _url
                    elif 'webm' in _url: return [True, _url]
                    elif 'thumbs' in _url: return [True, _url]
                    else:
                        _gfy = 'https://gfycat.com/gifs/detail/'+_url.split('/')[-1]

                    return [False, _url, '"gifUrl":"(.*?'+_url.split('/')[-1]+'.*?\.gif)"']

                elif re.search('vimeo.com', url_domain[0]):
                    resp = await self.aio_http.get(_url)
                    if resp.error:
                        return [False, False]

                    data = json.loads(resp.content.decode('utf8'))
                    _vimeo_thumb = False
                    try: _vimeo_thumb = data.get('thumbnail_url')
                    except: _vimeo_thumb = False

                    return [_vimeo_thumb, _vimeo_thumb]

                elif re.search('coub.com', url_domain[0]):
                    resp = await self.aio_http.get('https://coub.com/api/v2/coubs/'+_url.split('/')[-1])
                    if resp.error:
                        return [False, False]
                    data = json.loads(resp.content.decode('utf8'))
                    for ver in data.get('image_versions').get('versions'):
                        _coub_image = data.get('image_versions').get('template').format(version=ver).replace('%', '')
                        if ver == 'big':
                            break
                    return [True, _coub_image]

                elif re.search('giphy.com', url_domain[0]):
                    try:
                        _giphy = 'https://media.giphy.com/media/'+_url.split('/')[-1].split('-')[1]+'/giphy_s.gif'
                    except:
                        try:
                            _giphy = 'https://media.giphy.com/media/'+_url.split('/')[-1]+'/giphy_s.gif'
                        except: return [False, False]
                    return [True, _giphy]

                elif re.search('instagram.com', url_domain[0]):
                    return [False, _url, '<meta property="og:image" content="(.*?)"']

                elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:png|jpg|bmp|jpeg|gif)'), _url):
                    return [True, _url]

                elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:webm|mp4|avi|mpeg|3gp)'), _url):
                    return [True, _url]

                #logger.debug(f'new media: {_url}')
                return [False, _url]

            except:
                log_stack.info('check_domain')
                return [False, False]

    async def find_urls(self):
        links = []
        ex_links = []
        try:
            urls = []
            if not self.data:
                return []
            for s in self.recompile:
                r = re.findall(re.compile(s), self.data)
                if r:
                    urls.extend(r)
            urls = sorted(set(urls))
            #logger.info(f'urls: {urls}')

            for _url in urls:
                url = _url.replace('\\u002F', '/').replace('\\u0026', '&').replace('\\', '/')
                if self.what:
                    _ch = await self.check_domain(url)
                    if _ch[0]:
                        links.append(_ch[1])
                    else:
                        if len(_ch) == 3:
                            ex_links.append([_ch[1], _ch[2]])
                else:
                    links.append(url)

            if ex_links:
                _results = await self.aio_http.get_urls([[x[0], None] for x in ex_links])
                for resp, _regex in zip(_results, [x[1] for x in tuple(ex_links)]):

                    if not resp.error:
                        try:
                            links.append(
                                re.findall(
                                    re.compile(_regex),
                                    resp.content.decode('utf8'))[0].replace(
                                    '\u002F', '/').replace(
                                    '\u0026', '&'))
                        except:
                            log_stack.info(f'find_urls.re.compile: {resp.url}')
        except:
            log_stack.info('find_urls', exc_info=True, stack_info=True)

        self.links = links
        return self.ret()

    def ret(self):
        if isinstance(self.links, list):
            return self.links
        elif isinstance(self.links, str):
            return [self.links]
        else:
            return False

