import re

from log import logger


class KinozalVarsFinder:

    def kn_find_year(self, splitted_name):

        def split_dash(tt):
            return tt.split('-')[1]

        def split_brackets(tt):
            return tt.split('(')[1].split(')')[0]

        def split_comma(tt):
            return re.findall('\d+', tt.split(',')[-1])[0]

        year = None
        for yf in (
            split_dash, split_brackets,
            split_comma
        ):
            for tt in splitted_name[1:]:
                try:
                    _tmp = yf(tt)
                    if len(_tmp) != 4:
                        continue

                    year = int(_tmp)
                    break
                except (ValueError, IndexError):
                    continue

        if not year:
            raise ValueError

        return year


def test_find_year():
    for nm in (
            ('Выход есть (1-2 сезоны: 1-12 серии из 12) / Exit / 2019, 2021 / ДБ / WEB-DL (1080p)', 2021),
            ('Не отпускай меня (1-4 серии из 4) / 2013, СТ / WEBRip (720p)', 2013)
    ):
        name, year = nm
        splitted_name = name.split('/')

        assert KinozalVarsFinder().kn_find_year(splitted_name) == year
