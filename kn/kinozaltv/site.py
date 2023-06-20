from .details import DetailsPage
from .top import TopPage
from .browse import BrowsePage


class KinozalSite(
    DetailsPage,
    TopPage,
    BrowsePage,
):

    def __init__(self):
        self.load_cookies()
