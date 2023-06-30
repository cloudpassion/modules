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
                # logger.info(f'{key=}, {sub_keys=}')
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
                # if sub_keys:
                #     logger.info(f'{value_db_kwargs=}')

                string = self.calc_hash(
                    value,
                    value_db_kwargs
                )

            else:
                string = f'{value}'

            _strings.append(string)

        hash_object = hashlib.sha512(''.join(_strings).encode('utf8'))
        digest = hash_object.hexdigest()
        if digest == '2932afee7ee0905cf16602c4ce93373191948b8d561565629c88a492ce7bf4996b9ae2525cda8fdd438dfaa066924db0f8536d7912729f60ad21ae8186978701':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        return digest
