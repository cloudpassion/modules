from config import secrets

from .imdb import IMDBSite
from .kinorium import KinoriumSite
from .files import FromFiles


class GetMovies(
    IMDBSite,
    KinoriumSite,
    FromFiles,
):

    def __init__(
            self,
            kinorium_lang='ru',
    ):
        self.kinorium_config(lang=kinorium_lang)

        self.proxy = secrets.http.proxy.address
