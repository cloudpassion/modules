import time

from config import secrets

from atiny.reos.dir.create import create_dir


class GetMovDefault:

    def __init__(
            self,
    ):

        self.proxy = secrets.http.proxy.address

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'

    def write_resp_content(self, resp, fl='resp.html'):
        with open(f'{fl}', 'wb') as rwb:
            rwb.write(resp.content)

    def clear_title(self, title):

        for to_space in (
            '\xa0',
        ):
            title = title.replace(to_space, ' ')

        for to_zero in (
            '— ...', '—', "'", '"',
        ):
            title = title.replace(to_zero, '')

        return title

    def write_titles(
            self, to_dir, pre_name, titles
    ):

        create_dir(to_dir)

        with open(
                f'{to_dir}/{pre_name}_{time.strftime("%d.%m.%Y_%H.%M")}.txt',
                'w', encoding='utf8'
        ) as tw:
            tw.writelines(
                list(
                    [
                        f'{x}\n' for x in set(
                        [
                            self.clear_title(y) for y in titles
                        ]) if x
                    ]
                )
            )
