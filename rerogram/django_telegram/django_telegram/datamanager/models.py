from config import settings, secrets

from .default import TimeBasedModel

from .tg.chat import *
from .tg.user import *
from .tg.files import *
from .tg.message import *
from .tg.stuff import *
from .tg.discuss import *
from .spbportal.spb_models import *

# from .tg.bot import *
# from .shop.items import *
#
#

__all__ = []

from .tg import chat
__all__.extend(chat.__all__)
from .tg import user
__all__.extend(user.__all__)
from .tg import files
__all__.extend(files.__all__)
from .tg import message
__all__.extend(message.__all__)
from .tg import stuff
__all__.extend(stuff.__all__)
from .tg import discuss
__all__.extend(discuss.__all__)
from .spbportal import spb_models as spbportal_models
__all__.extend(spbportal_models.__all__)

# from .tg import bot
# __all__.extend(bot.__all__)
# from .shop import items
# __all__.extend(items.__all__)





