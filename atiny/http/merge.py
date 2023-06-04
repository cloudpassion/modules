
try:
    from log import logger
except ImportError:
    from atiny.log import logger


# merge different http responses to one
class MergeResp:
    def __init__(
            self, text=r'', content=b'', headers=None, status=0, url=None,
            error=True, proxy=None, path=None, request_headers=None, log=''):

        self.text = text
        self.status = status
        self.content = content
        self.headers = headers if headers else {}
        self.cookies = {}
        self.url = url
        self.error = error
        self.proxy = proxy
        self.path = path
        self.request_headers = request_headers if request_headers else {}
        self.log = log
