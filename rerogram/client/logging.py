import pyrogram

from typing import Union

from log import logger
from config import settings


class MyPyrogramLogging:

    log_session_file: str

    def log_event(self, event):
        if not settings.log.log_session:
            return

        # TODO: remake to any
        if hasattr(event, 'chat') and hasattr(event.chat, 'id'):
            for _id in settings.log.skip:
                if event.chat.id == _id:
                    return

        logger.info(f'event.type: {type(event)}\n{event=}\n')

    def save_event(self, event):
        if not settings.log.save_session:
            return

        try:
            json_update = event.to_json()
            with open(self.log_session_file, 'a') as lsa:
                lsa.write(f'{json_update}\n')
        except AttributeError:
            return

