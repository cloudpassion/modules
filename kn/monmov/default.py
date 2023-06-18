import os

from atiny.http import MyHttp
from config import secrets


class MonMovDefault:

    def __init__(
            self,
    ):

        self.proxy = secrets.http.proxy.address

    async def download_images(self, images):
        jpgs = []
        for _n, scr in enumerate([
            *images,
        ]):
            n = _n + 1
            if not scr:
                try:
                    os.remove(f'{n}.jpg')
                except Exception:
                    pass

                continue

            if len(jpgs) >= 10:
                break

            http = MyHttp(
                save_cache=True, save_headers=False
            )
            resp = await http.get(
                url=scr, tmp_dir='.', path=f'{n}.jpg'
            )
            if not resp.error and resp.status == 200:
                jpgs.append(f'{n}.jpg')
            else:
                try:
                    os.remove(f'{n}.jpg')
                except Exception:
                    pass

        return jpgs
