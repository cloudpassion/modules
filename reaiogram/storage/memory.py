from aiogram.contrib.fsm_storage.memory import MemoryStorage as DefaultMemoryStorage


class MemoryStorage(DefaultMemoryStorage): pass


class ThreadMemoryStorage(DefaultMemoryStorage): pass