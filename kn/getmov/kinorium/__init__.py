from .filmlist import KinoriumFilmListSite
from .premiere import KinoriumPremierSite


class KinoriumSite(
    KinoriumFilmListSite,
    KinoriumPremierSite
):
    pass
