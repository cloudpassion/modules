from config import secrets

from .kinozal import KinozalMonitor
from .tgx import TgxMonitor


class KinoMovieMonitor(
    KinozalMonitor,
    TgxMonitor,
):

    pass
