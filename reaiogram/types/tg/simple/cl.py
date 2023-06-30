from log import logger


class SimpleCl:

    def __init__(self, db_class, cl: object):

        for key in db_class.db_keys:
            self._set_not_none(self, key, cl)
            if not hasattr(cl, key):
                continue

            if not getattr(cl, key):
                continue

            att = getattr(cl, key)
            if isinstance(att, (int, str, )):
                setattr(self, key, att)
            else:

                try:
                    annotations = getattr(att, '__annotations__')
                except AttributeError:
                    continue

                sub_d = {}
                for sub_key in annotations:
                    logger.info(f'{sub_key=}')

                    sub_att = getattr(att, sub_key)
                    if isinstance(sub_att, (int, str, )):
                        sub_d[sub_key] = sub_att

                for k, v in sub_d:
                    setattr(att, k, v)

                setattr(self, key, att)

    def _set_not_none(self, simple_cl, key, cl):
        if not hasattr(cl, key):
            return

        if getattr(simple_cl, key):
            return

        setattr(simple_cl, key, getattr(cl, key))

    def _del_none(self, key, cl):

        if not hasattr(cl, key):
            return

        if getattr(cl, key):
            return

        else:
            delattr(cl, key)
