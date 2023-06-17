import random
import asyncio

try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback

from .main import MyHttp


class MyHttpMulti(
    MyHttp
):

    async def get_urls_semaphore(self, tasks_timeouts, command):

        async with self.sem:
            if tasks_timeouts:
                _sleep = random.randint(tasks_timeouts[0], tasks_timeouts[1])
                await asyncio.sleep(_sleep)

            task_result = await command

            return task_result

    async def get_urls(
            self, links, max_tasks=100, tasks_timeouts=None,
            ssl_cert=None, headers=None,
            tmp_dir='.tmp'
    ):

        #logger.info(links)
        _headers_file = None
        tasks = []
        self.sem = asyncio.Semaphore(max_tasks)

        for link in links:
            _headers = {}
            _path = None
            if isinstance(link, list) or isinstance(link, tuple):
                _url = link[0]
                try:
                    _path = link[1]
                except IndexError:
                    pass

                if len(link) >= 3:
                    if isinstance(link[2], str):
                        _headers_file = link[2]
                    elif isinstance(link[2], dict):
                        _headers = link[2]
                    else:
                        pass

                if len(link) >= 4:
                    _save_override = link[3]
                else:
                    _save_override = False
            else:
                _url = link
                _save_override = False
                _headers_file = None

            if not _path:
                #_path = _url.split('/')[2:3][0]
                _path = '.'.join(_url.split('/')[3:])

            #logger.info(f'get_urls:url: {_url}, path: {tmp_dir + _path}')

            if not _headers_file:
                _headers_file = _path+'.request_headers'
            if not _headers:
                if headers:
                    _headers = headers
                else:
                    _headers = self.cache_class.headers_detect(
                        'load', headers_data=_headers_file)
            #tasks.append(
            #    asyncio.create_task(
            #        MyHttp(proxy=self.proxy).get(
            #            url=_url, path=_path, headers=_headers, tmp_dir=tmp_dir)
            #    )
            #)
            tasks.append(
                asyncio.create_task(self.get_urls_semaphore(
                    tasks_timeouts,
                    MyHttp(
                        proxy=self.proxy, ssl_cert=ssl_cert, version=self.version,
                        save_headers=self.save_headers,
                    ).do(
                        'get',
                        url=_url, path=_path, headers=_headers, tmp_dir=tmp_dir)
                )
                )
            )

        results = await asyncio.gather(*tasks)

        for result in results:
            if not result:
                continue
            if not result.error:
                if result.status != 200:
                    logger.info(f'url: |{result.url}| content: {result.content}\n\n'
                                f's_headers: {result.headers}\n\n'
                                f'status: {result.status}\n\n')

                self.cache_class.save_after_resp(merge_resp=result, update_cookies=True)

            else:
                logger.info(f'bad result: {result}')

        return results

