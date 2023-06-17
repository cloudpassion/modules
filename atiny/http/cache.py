import os
import pathlib

from typing import Union

try:
    from log import logger
except ImportError:
    from ..log import logger


from .utils import MyHttpUtils
from ..reos.file.data import DataFile
from .merge import MergeResp


class MyHTTPCache:

    resp_data_file_postfix: str = '.resp_data'
    headers_file_postfix: str = '.resp_data'

    def __init__(self, save_cache=False, load_cache=False, save_headers=False):
        self.save_cache = save_cache
        self.load_cache = load_cache
        self.save_headers = save_headers

    def headers_detect(
            self, operation,
            headers_data=Union[dict, str],
            save_data=Union[dict, str],
            update=True
    ):

        if operation == 'save':
            if self.save_headers:
                file_data = DataFile(headers_data)
                file_data.save(save_data, update=update)

        elif operation == 'load':
            file_data = DataFile(headers_data)
            js = file_data.load()

            if js:
                _headers = js.get('request_headers')

                if _headers.get('Cookie'):
                    _cookies = {'Cookie': _headers.get('Cookie')}
                    _headers.update(_cookies)
            else:
                return {}

            return _headers

        elif operation == 'update':
            _heads = save_data.copy()
            _server_headers = headers_data.copy()
            _set_cookies = '; '.join(
                [v.split(';')[0] for k, v in _server_headers.items() if k == 'Set-Cookie']
            )
            if not _set_cookies:
                _set_cookies = {}

            if 'Set-Cookie' in _server_headers and _set_cookies != save_data.get('Cookie'):
                _heads.update({'Cookie': _set_cookies})
                return _heads

            return _heads

    def load_content(self, path='.test.http.html', url=None, tmp_dir='.tmp'):

        if not self.load_cache:
            return None

        if path and isinstance(path, str):
            path = f'{tmp_dir}/{path}'
        else:
            path = MyHttpUtils().make_path(url, tmp_dir=tmp_dir)

        if not os.path.isfile(path):
            logger.info(f'load_content non existing path: {path}')
            return None

        js_data = DataFile(f'{path}.{self.resp_data_file_postfix}')
        js = js_data.load()

        _status = js.get('status_code') if 'status_code' in js else 0
        _headers = self.headers_detect(
            'load', headers_data=f'{path}.{self.headers_file_postfix}'
        )

        with open(path, 'rb') as crb:
            _content = crb.read()

        return MergeResp(
            text='', content=_content, headers=_headers, status=_status,
            path=path, url=url, error=False,
        )

    def save_content(
            self,
            save_resp=False, save_headers=False, merge_resp=None
    ):

        if not self.save_cache and not self.save_headers:
            return None

        if merge_resp:

            if not merge_resp.error:
                MyHttpUtils().make_dirs(merge_resp.path)

                pathlib.Path(
                    os.path.dirname(
                        os.path.abspath(merge_resp.path))).mkdir(parents=True, exist_ok=True)

                if save_resp:

                    with open(merge_resp.path, 'wb') as fw:
                        fw.write(merge_resp.content)

                return

            """ try save server_headers if request failed with not 200 http.code """
            if merge_resp.headers and (save_headers or self.save_headers):

                file_data = DataFile(merge_resp.path)
                data = {
                    'status_code': merge_resp.status,
                    'request_headers': merge_resp.request_headers,
                    'server_headers': {k: v for k, v in merge_resp.headers.items()},
                }
                file_data.save(data, update=True)

    def save_after_resp(
            self, merge_resp: MergeResp = None, update_cookies=False
    ):

        if not self.save_cache and not self.save_headers:
            return

        if merge_resp:
            self.save_content(
                save_resp=self.save_cache, save_headers=self.save_headers,
                merge_resp=merge_resp)

            _headers = merge_resp.request_headers
            _set_cookies = '; '.join(
                [v.split(';')[0] for k, v in merge_resp.headers.items() if k.lower() == 'set-cookie']
            )
            merge_resp.cookies.update(
                {
                    v.split(';')[0].split('=')[0]: v.split(';')[0].split(
                        '='
                    )[1] for k, v in merge_resp.headers.items() if k.lower() == 'set-cookie'
                }
            )

            if update_cookies:
                if merge_resp.headers.get(
                        'Set-Cookie'
                ) and _set_cookies != merge_resp.request_headers.get('Cookie'):
                    _headers.update({'Cookie': _set_cookies})

            self.headers_detect(
                'save', f'{merge_resp.path}.{self.headers_file_postfix}',
                save_data={
                    'status_code': merge_resp.status,
                    'request_headers': _headers,
                    'server_headers': {k: v for k, v in merge_resp.headers.items()},
                },
                update=False
            )

            return self.headers_detect(
                'update', merge_resp.headers, merge_resp.request_headers
            )


