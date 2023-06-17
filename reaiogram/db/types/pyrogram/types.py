# import pyrogram.enums
# import pyrogram.types

from typing import Union, List

# from pyrogram.raw.types.channel import Channel
# from pyrogram import Client as PyrogramClient
# from pyrogram.types import (
#     User as PyrogramUser,
#     Chat as PyrogramChat,
#     Message as PyrogramMessage,
#     List as PyrogramList
# )


from ....django_telegram.django_telegram.datamanager.models import (
    # TgPoll as DjangoTelegramPoll,
    TgMessage as DjangoTelegramMessage,
)

# MESSAGE_TYPES = Union[
#     # pyrogram
#     PyrogramMessage, DjangoTelegramMessage,
#     List[PyrogramMessage], List[DjangoTelegramMessage],
# ]
#
# SERVICE_TYPES = {
#     # pyrogram
#     **{k: k.value for k in list(pyrogram.enums.MessageServiceType)},
#     **{k.value: k for k in list(pyrogram.enums.MessageServiceType)},
# }
#
# POLL_TYPES = {
#     # pyrogram
#     **{k: k.value for k in list(pyrogram.enums.poll_type.PollType)},
#     **{k.value: k for k in list(pyrogram.enums.poll_type.PollType)},
# }
