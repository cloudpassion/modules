import calendar

from datetime import datetime


def get_last_day():

    dt = datetime.now()
    year = dt.year
    month = dt.month

    return calendar._monthlen(year, month)
