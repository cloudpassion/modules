import os

from glob import glob


try:
    from log import logger, log_stack
except ImportError:
    from atiny.log import logger, log_stack


class FromFiles:

    def get_year_titles(self, year):
        if os.path.isfile(
            f'files/{year}.txt'
        ):
            with open(
                    f'files/{year}.txt', 'r',
                    encoding='utf8'
            ) as fr:
                lines = fr.readlines()

            return [x.splitlines()[0] for x in lines]

        return []

    def merge_year_files(self, year):
        files = glob(f'files/*/{year}*')

        titles = set()
        for fl in files:
            logger.info(f'{fl=}')

            with open(
                    fl, 'r', encoding='utf8'
            ) as fr:
                lines = fr.read()

            for line in lines.splitlines():
                logger.info(f'{line=}')
                titles.add(line.splitlines()[0])

        with open(
            f'files/{year}.txt', 'w',
            encoding='utf8'
        ) as yw:
            yw.write(
                '\n'.join(list(titles))
            )



