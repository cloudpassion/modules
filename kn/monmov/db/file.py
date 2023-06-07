import os

FDB_ALL = 'all.txt'
IMDB_ALL = 'all_imdb.txt'


class FileDB:

    def fdb_add_parsed(self, text):
        with open(FDB_ALL, 'a', encoding='utf8') as aa:
            aa.write(
                f'{text}\n'
            )

    def fdb_add_imdb(self, text):
        with open(IMDB_ALL, 'a', encoding='utf8') as aa:
            aa.write(
                f'{text}\n'
            )

    def fdb_get_skip(self, where):
        if where == 'imdb':
            fl = IMDB_ALL

        if os.path.isfile(fl):
            with open(fl, 'r', encoding='utf8') as ar:
                lines = ar.readlines()

            return [x.splitlines()[0].split('|')[0] for x in lines]

        else:
            return []

    def fdb_get_skip_names(self):
        if os.path.isfile(FDB_ALL):
            with open(FDB_ALL, 'r', encoding='utf8') as ar:
                lines = ar.readlines()

            return [x.splitlines()[0].split('|')[0] for x in lines]

        else:
            return []

    def fdb_get_skip_titles(self, year):
        if os.path.isfile('als.txt'):
            with open(
                    'als.txt', 'r',
                    encoding='utf8'
            ) as ar:
                lines = ar.readlines()

            return [x.splitlines()[0] for x in lines]

        else:
            return []


