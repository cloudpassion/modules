try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger
except ImportError:
    from atiny.log import logger

from config import secrets

from bs4 import BeautifulSoup

from atiny.http import MyHttp
from atiny.http.utils import MyHttpUtils

from kn.getmov.default import GetMovDefault


class TGxParse(
    GetMovDefault
):
    pass
