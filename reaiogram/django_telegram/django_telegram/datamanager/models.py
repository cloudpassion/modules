from config import settings, secrets

from .default import ExtraBasedModel

from .tg.chat import *
from .tg.user import *
from .tg.message import *
from .tg.file import *

from .tg.discuss import *

__all__ = []

from .tg import chat
__all__.extend(chat.__all__)
from .tg import user
__all__.extend(user.__all__)
from .tg import message
__all__.extend(message.__all__)
from .tg import file
__all__.extend(file.__all__)

from .tg import discuss
__all__.extend(discuss.__all__)

