import re

from log import logger

from .default import DefaultBot


class RequestsHandlerBot(DefaultBot):

    @staticmethod
    def get_retry_timeout(exc):
        searches = [
            re.compile('Retry in (.*?) seconds'),
            re.compile("retry after (.*?)'"),
            re.compile('retry after (.*?)'),
            re.compile('\d+'),
        ]
        tm = 50
        for search in searches:
            try:
                tm = int(re.findall(search, f'{exc}')[0])
                break
            except ValueError:
                pass
            except IndexError:
                pass
            except Exception as exc:
                logger.info(f'{search=}, {exc=}')
                continue

        if tm == 50:
            logger.info(f'{exc=}')

        return tm
