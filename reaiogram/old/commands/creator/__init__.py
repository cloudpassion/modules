from aiogram.dispatcher.filters import Command
from config import settings, secrets


creator_commands = Command(
    commands=secrets.creator.commands, ignore_case=True, ignore_caption=True
)
