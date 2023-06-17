import calendar

from collections import namedtuple
from datetime import datetime, timedelta, timezone


def get_last_day():

    dt = datetime.now()
    year = dt.year
    month = dt.month

    return calendar._monthlen(year, month)


def dt_parse(datetime=None, settings=None):

    if settings:
        timezone_offset = settings.timezone_offset
        timezone_name = settings.timezone_name
        timezone_timedelta = timedelta(hours=timezone_offset)
    else:
        timezone_timedelta = timedelta()

    human = None

    if datetime is None:
        datetime = datetime.now()
        # datetime = datetime.now(
        #         tz=timezone(
        #             offset=timedelta(hours=timezone_offset),
        #             name=timezone_name
        #         )
        #     )

    original = datetime

    if settings:
        work_date = datetime + timezone_timedelta
    else:
        work_date = datetime

    human = work_date.strftime(
        '%d.%m.%Y %H:%S'
    )

    parsed_date = namedtuple(
        'human', 'original', 'work'
    )

    return parsed_date._make(
        (human, original, work_date)
    )
