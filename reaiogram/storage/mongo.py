from aiogram.contrib.fsm_storage.mongo import MongoStorage as DefaultMongoStorage


class MongoStorage(DefaultMongoStorage): pass


class ThreadMongoStorage(DefaultMongoStorage): pass