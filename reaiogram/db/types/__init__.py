from .user import MergedTelegramUser, MergedAiogramUser
from .chat import MergedAiogramChat, MergedTelegramChat
from .message import MergedTelegramMessage, MergedAiogramMessage

from .file.document import MergedAiogramDocument, MergedTelegramDocument


MERGED_TG_CLASSES = [
    MergedTelegramUser,
    MergedAiogramUser,

    MergedAiogramChat,
    MergedTelegramChat,

    MergedAiogramMessage,
    MergedTelegramMessage,

    MergedAiogramDocument,
    MergedTelegramDocument,
]
