from .tg.bot import *
from .tg.update import *
from .tg.chat import *
from .tg.user import *
from .tg.message import *
from .tg.file import *

from .bt import *

from .tg.discuss import *

from .tg import bot, update
from .tg import chat, user
from .tg import message
from .tg import file
from .tg import discuss

from .bt import torrent, piece


__all__ = []

# tg
__all__.extend(bot.__all__)
__all__.extend(update.__all__)
__all__.extend(chat.__all__)
__all__.extend(user.__all__)
__all__.extend(message.__all__)
__all__.extend(file.__all__)
__all__.extend(discuss.__all__)

# bt
__all__.extend(torrent.__all__)
__all__.extend(piece.__all__)


