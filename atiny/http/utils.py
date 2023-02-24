
class MyHttpUtils:

    def get_ua(self):
        return 'Mozilla/5.0 (X11; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'

    def make_path(self, url, tmp_dir=''):
        if url:
            ret = url.replace(
                ':', '.'
            ).replace('?', '.').replace('/', '.').replace('&', '.')[0:200]
        else:
            ret = None

        return tmp_dir + ret if tmp_dir and isinstance(
            tmp_dir, str
        ) and isinstance(ret, str) else ret
