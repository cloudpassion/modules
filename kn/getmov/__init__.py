from .imdb import IMDBSite
from .kinorium import KinoriumSite
from .files import FromFiles


class GetMovies(
    IMDBSite,
    KinoriumSite,
    FromFiles,
):
    pass
