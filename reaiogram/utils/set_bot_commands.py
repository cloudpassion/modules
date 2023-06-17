from aiogram import types

from config import settings


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            *[types.BotCommand(x, f'info about: {x}') for x in settings.aiogram.extra_commands],
            types.BotCommand("help", "Вывести справку"),
        ]
    )
