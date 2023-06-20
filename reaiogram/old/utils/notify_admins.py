from typing import Optional

from config import secrets
from reaiogram.dispatcher.default import Dispatcher
from log import mlog, log_stack


async def on_startup_notify(dp: Dispatcher):

    admins = secrets.aiogram.admins if secrets.aiogram.admins else []
    try:
        creator = secrets.creator.id
    except AttributeError:
        creator = None

    if creator and creator not in admins:
        try:
            await dp.bot.send_message(creator, "Bot started")
        except Exception:
            log_stack.info(f'notify {creator=}')

    for admin in admins:
        try:
            await dp.bot.send_message(admin, "Bot started")
        except Exception:
            log_stack.info(f'notify {admin=}')
