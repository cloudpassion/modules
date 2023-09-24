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

        if digest == '8987c091b54b350a7dc6726f8bfa788bb5120e4722716c3434e3fc1e21afaa1b2440fd292c2f1d8cf7a1a9f432a1bf5cfe4911ce699261a32077ee1b41b86c38':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == '7afc80a6818dae08313a194c28078a79657587c3b30dd7d7183f4d3f31390efed23bd4242a23e72f7683bec417c46045869e5ce6acbd87e92a5209da90b08e26':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == 'ef81b4bb107185d302d6f3ca8f0acd8375ddd099d8a8b17a419143da691e26147459fb4fdb10db8817820955efbfac5c7fc87af7fcf0a43b3ff233c1e88befda':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == '2932afee7ee0905cf16602c4ce93373191948b8d561565629c88a492ce7bf4996b9ae2525cda8fdd438dfaa066924db0f8536d7912729f60ad21ae8186978701':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == '34f432db71146bdba531c6887ef458f6cbf7083cf8ab537db84a5f9c727833ae5e4732d3c3f4c8300f4ae72fb70a37cddae156562e9ebdbb1d277bd42c112b04':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == '1c0a6d013e2bf7bd39505606ec037ff4371e06853b6c4fbafd7369275146456fcdcb8ed365b8690dee7442ca57bdf031a1e00457cfefebdc49c80f816374cda1':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')

        if digest == '86f8f5d40e3f1ff2d1e65637bd73091e9bf19e8ca897a00183306bb3641e6b0ffac6d3bbf698e2324a104677d4595c3da4245b5b13ebaf5853e36dca5a1427cb':
            logger.info(f'{_strings=}')
            logger.info(f'{db_kwargs=}')


        return digest
