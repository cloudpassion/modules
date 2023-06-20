
class VarsFinder:

    keys: list

    def set_locals(self, _locals):

        if not hasattr(_locals, 'items'):
            throw = {
                k: getattr(_locals, k) for k in _locals.keys if hasattr(_locals, k)
            }
        else:
            throw = _locals

        for key, value in throw.items():
            if key in self.keys:
                setattr(self, key, value)
                # logger.info(f'{key}:{value}')
