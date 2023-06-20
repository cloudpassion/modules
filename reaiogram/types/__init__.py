
from reaiogram.types.tg.bot import MergedAiogramBot, MergedTelegramBot
from reaiogram.types.tg.update import MergedAiogramUpdate, MergedTelegramUpdate

from reaiogram.types.tg.user import MergedTelegramUser, MergedAiogramUser
from reaiogram.types.tg.chat import MergedAiogramChat, MergedTelegramChat
from reaiogram.types.tg.message import MergedTelegramMessage, MergedAiogramMessage

from reaiogram.types.tg.file import MergedAiogramDocument, MergedTelegramDocument


MERGED_TG_CLASSES = [
    MergedAiogramBot,
    MergedTelegramBot,

    MergedAiogramUpdate,
    MergedTelegramUpdate,

    MergedAiogramUser,
    MergedTelegramUser,

    MergedAiogramChat,
    MergedTelegramChat,

    MergedAiogramMessage,
    MergedTelegramMessage,

    MergedAiogramDocument,
    MergedTelegramDocument,
]
