from pathlib import Path

from ..file import FileUtils

from log import log_stack, logger


class ReqHTTPCache:

    def __init__(self, save_cache=False, load_cache=False):
        self.save_cache = save_cache
        self.load_cache = load_cache

    def save_after_resp(
            self,
            merge_resp=None, update_cookies=False,
            path=None, tmp_dir='',
    ):

        if not self.save_cache:
            return

        if merge_resp and not merge_resp.error:

            if path and isinstance(path, str):
                path = tmp_dir+path
            else:
                path = MyHttpUtils().make_path(url, tmp_dir=tmp_dir)

            try:
                self.save_content(
                    save_resp=self.save_cache,
                    save_headers=self.save_cache,
                    merge_resp=merge_resp
                )

                _headers = merge_resp.request_headers
                _set_cookies = '; '.join(
                    [
                        v.split(';')[
                            0
                        ] for k, v in merge_resp.headers.items() if k == 'Set-Cookie'
                    ]
                )
                merge_resp.cookies.update(
                    {
                        v.split(';')[0].split('=')[0]: v.split(';')[0].split('=')[1] for k, v in merge_resp.headers.items() if k == 'Set-Cookie'
                    }
                )

                if update_cookies:
                    if merge_resp.headers.get(
                            'Set-Cookie') and _set_cookies != merge_resp.request_headers.get(
                        'Cookie'
                    ):
                        _headers.update({'Cookie': _set_cookies})

                data = self.make_data(
                    'save', merge_resp.path,
                    headers=_headers,
                    status=merge_resp.status,
                    update=False
                )
                data.update(
                    self.make_data(
                        'update',
                        headers=data['server']
                    )
                )
                return data

                return self.headers_detect(
                    'update', merge_resp.headers, merge_resp.request_headers
                )
            except Exception:
                log_stack.info('MyHTTPCache.save_after_resp')

    def update_headers(self, server_headers, request_headers):
        _set_cookies = '; '.join(
            [v.split(';')[0] for k, v in server_headers.items() if k.lower() == 'Set-Cookie']
        )
        if not _set_cookies:
            _set_cookies = {}

        if (
                'Set-Cookie' in server_headers
        ) and (
                f'{_set_cookies}' != f"{request_headers.get('Cookie')}"
        ):
            request_headers.update({
                'Cookie': _set_cookies,
            })

    def load_data(self):
        _headers = FileUtils(_load_json_from_file(headers_data)
        if _headers.get('Cookie'):
            _cookies = {'Cookie': _headers.get('Cookie')}
            _headers.update(_cookies)
        return _headers

    def headers_detect(self, operation, headers_data={}, save_data={}, update=True):

        if operation == 'save':
            return headers_data, save_data, update



    def load_content(self, path='.test.http.html', url=None, tmp_dir=''):

        if not self.load_cache:
            return None


        if not os.path.isfile(path):
            logger.info(f'load_content not path: {path}')
            return None
        else:
            _json = _load_json_from_file(path + '.status_code')
            _status = _json.get('status') if _json else 0
            _headers = self.headers_detect(
                'load', headers_data=path+'.server_headers')

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

        if not self.save_cache:
            return None

        if merge_resp and not merge_resp.error:

            if save_resp:
                #logger.info(f'spath: {merge_resp.path}')
                Path(
                    os.path.dirname(
                        os.path.abspath(
                            merge_resp.path
                        ))).mkdir(parents=True, exist_ok=True)

                #logger.info(f'save_content: {merge_resp.path}')
                with open(merge_resp.path, 'wb') as fw:
                    fw.write(merge_resp.content)

            """ try save server_headers if request failed with not 200 http.code """
            if save_headers:
                pathlib.Path(
                    os.path.dirname(
                        os.path.abspath(merge_resp.path))).mkdir(parents=True, exist_ok=True)
                with open(merge_resp.path + '.server_headers', 'w') as sw, \
                        open(merge_resp.path + '.status_code', 'w') as cw:
                    try:
                        sw.write(json.dumps({k: v for k, v in merge_resp.headers.items()}))
                        cw.write(json.dumps({'status': merge_resp.status}))
                    except Exception as _tr:
                        log_stack.info('save_content')
