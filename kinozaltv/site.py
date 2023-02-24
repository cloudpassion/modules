from .details import DetailsPage


class KinozalSite(
    DetailsPage,
):

    def __init__(self):
        self.load_cookies()
