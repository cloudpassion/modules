from aiogram import types
from log import logger

from config import settings
from aiogram import Dispatcher

async def set_default_commands(dp):
    return
    # dp: Dispatcher
    # logger.info(f'{dir(dp)}')

    # await dp.bot.set_my_commands(
    #     [
    #         *[types.BotCommand(x, f'info about: {x}') for x in settings.aiogram.extra_commands],
    #         types.BotCommand("help", "Вывести справку"),
    #     ]
    # )
