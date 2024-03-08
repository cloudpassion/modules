from aiogram.enums.update_type import UpdateType

MESSAGE_UPDATE_TYPES = [x for x in UpdateType if 'message' in x or 'channel' in x]
UPDATE_TYPES = [x for x in UpdateType]

# 20MB
MAX_FILE_SIZE = 20971520
# 50MB, TODO: very slow telethon download, even with cryptg
# MAX_FILE_SIZE = 52428800
