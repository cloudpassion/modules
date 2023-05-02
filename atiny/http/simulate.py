try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback

try:
    import requests
except ImportError:
    logger.info(f'need install requests for MyRequestsHTTP')


from .merge import MergeResp
from .utils import MyHttpUtils


try:
    import responses
    @responses.activate
    def requests_simulate(
            url='http://ggg', code=200, response=None, content_type='text/plain',
            proxy=None, path=None, tmp_dir='.tmp'
    ):

        try:
            js = json.dumps(response)
            text = None
        except json.JSONDecodeError:
            js = None
            text = response

        if js:
            responses.add(responses.GET, url,
                          json=js, status=code)
        else:
            responses.add(responses.GET, url,
                          body=text, status=code,
                          content_type=content_type)

        _resp = requests.get(url)

        return MergeResp(
            _resp.text, _resp.content, _resp.headers, _resp.status_code, _resp.url,
            path=f'{tmp_dir}/'
                 f'{path}' if path and isinstance(
                path, str
            ) else MyHttpUtils().make_path(
                url, tmp_dir=tmp_dir,
            ),
            proxy=proxy, error=False
        )


except ImportError:
    pass
