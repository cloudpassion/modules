import hashlib

from log import logger


class DbFunctions:

    hash_strings: dict

    def calc_hash(self, db_class, db_kwargs):

        hash_keys = self.hash_strings[db_class.hash_key]

        _strings = []

        for key in hash_keys:
            # db_kwargs: # (*hash_keys, ): #*extra):
            if '.' in key:
                _key = key.split('.')[0]
                sub_keys = key.replace(f'{_key}.', '').split('.')
                key = _key
                # logger.info(f'{sub_keys=}')
            else:
                sub_keys = []

            try:
                value = db_kwargs[key]
            except KeyError:
                value = None

            if hasattr(value, 'hash_key'):
                if not sub_keys:
                    value_keys = value.db_keys
                else:
                    value_keys = sub_keys

                value_db_kwargs = {
                    key: getattr(
                        value, key
                    ) for key in value_keys if hasattr(value, key)
                }

                string = self.calc_hash(
                    value,
                    value_db_kwargs
                )

            else:
                string = f'{value}'

            _strings.append(string)

        hash_object = hashlib.sha512(''.join(_strings).encode('utf8'))
        return hash_object.hexdigest()


def test_calc_hash():

    cl = DbFunctions()
    cl.hash_strings = {}
    cl.hash_strings['temp'] = ['info_hash', 'torrent.info_hash']

    class TempCl: pass

    tmp_cl = TempCl()

    setattr(tmp_cl, 'hash_key', 'temp')

    cl.calc_hash(
        tmp_cl,
        {
            'info_hash': '213asdfasdf',
            'torrent': {
                'info_hash': 'avzxcvzxcvxc',
            }
        }
    )
