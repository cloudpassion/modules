import re

from log import logger

from ..stuff.find_vars import VarsFinder


class TgxVarsFinder(
    VarsFinder
):

    def tgx_find_year(self, splitted_name):

        def split_dot(tt):
            return tt.split('.')

        def no_split(tt):
            return tt

        # def split_dash(tt):
        #     return tt.split('-')[1]
        #
        # def split_brackets(tt):
        #     return tt.split('(')[1].split(')')[0]
        #
        # def split_comma(tt):
        #     return re.findall('\d+', tt.split(',')[-1])[0]

        year = None
        for yf in (
            no_split,
            split_dot,
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
            logger.info(f'{splitted_name=}')
            raise ValueError

        return year
#
#
# def test_find_year():
#     for nm in (
#             'Выход есть (1-2 сезоны: 1-12 серии из 12) / Exit / 2019, 2021 / ДБ / WEB-DL (1080p)',
#
#     ):
#         splitted_name = nm.split('/')
#
#         assert KinozalVarsFinder().kn_find_year(splitted_name) == 2021
