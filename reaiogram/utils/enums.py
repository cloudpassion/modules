from aiogram.enums.update_type import UpdateType

MESSAGE_UPDATE_TYPES = [x for x in UpdateType if 'message' in x or 'channel' in x]
UPDATE_TYPES = [x for x in UpdateType]
