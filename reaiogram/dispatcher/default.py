import asyncio

from typing import Union, Optional

# from reaiogram.db import LessonSqliteDatabase, \
#     LessonPostgreSqlDatabase
from ..db import MyDjangoORM

from aiogram import Dispatcher as DefaultDispatcher
from aiogram import types
from aiogram.fsm.storage.memory import BaseStorage
from aiogram import exceptions

from log import mlog, logger
from config import settings, secrets
from ..utils.misc import rate_limit

# from reaiogram.db.schemas.lesson.models import LessonChatModel
# 
# from reaiogram.db.schemas import LessonPostgreSqlGino, LessonDjangoORM, Task5DjangoORM
# from reaiogram.utils.task5_items_create import create_default_items

# from reaiogram.db.api.lesson.gino_sql import db as gino_db


class Dispatcher(DefaultDispatcher):

    handlers_to_register = set()

    def __init__(self, bot, loop=None,
                 storage: Optional[BaseStorage] = None,
                 run_tasks_by_default: bool = False,
                 throttling_rate_limit=settings.aiogram.DEFAULT_RATE_LIMIT, no_throttle_error=False,
                 filters_factory=None,
                 ):

        self.sql: Union[
            MyDjangoORM, None
        ] = None

        # super().__init__(
        #     bot, loop=loop, storage=storage,
        #     run_tasks_by_default=run_tasks_by_default, throttling_rate_limit=throttling_rate_limit,
        #     no_throttle_error=no_throttle_error,
        #     filters_factory=filters_factory
        # )
        super().__init__(
            storage=storage,
            # fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
            # events_isolation: Optional[BaseEventIsolation] = None,
            # disable_fsm: bool = False,
            # name: Optional[str] = None,
            # **kwargs: Any,
        )

    async def get_extra_info(self):
        return

    async def init_database(self, db):

        self.sql = db
        mlog.info(f'db: {db}, td: {type(db)}\n'
                 f'----------------------')

        if isinstance(db, MyDjangoORM):
            await db.create(
                host=secrets.db.host, database=secrets.db.name,
                user=secrets.db.user, password=secrets.db.password,
                port=secrets.db.port
            )

            #await db.drop_users()
            # await db.create_table_users()
            # r = await db.select_all_users()
            # mlog.info(f'pre: {r=}')
            # z = await db.add_user('nick1', 'Full1', 1213123)
            # await db.add_user('nick2', 'Full2', 31213123)
            # await db.add_user('nick3', 'Full3', 31213123)

            # r = await db.select_all_users()
            # mlog.info(f'post: {r=}')

        # if isinstance(db, LessonSqliteDatabase):
        #     try:
        #         await db.create_table_users()
        #     except Exception as exp:
        #         mlog.info(f'{exp=}')
        #
        #     mlog.info(f'{await db.select_all_users()}')
        # elif isinstance(db, LessonPostgreSqlDatabase):
        #     await db.create(
        #         host=secrets.db.host, asdfasdf=secrets.db.name,
        #         user=secrets.db.user, password=secrets.db.password,
        #         port=secrets.db.port
        #     )
        #
        #     #await db.drop_users()
        #     await db.create_table_users()
        #     r = await db.select_all_users()
        #     mlog.info(f'pre: {r=}')
        #     z = await db.add_user('nick1', 'Full1', 1213123)
        #     await db.add_user('nick2', 'Full2', 31213123)
        #     await db.add_user('nick3', 'Full3', 31213123)
        #
        #     r = await db.select_all_users()
        #     mlog.info(f'post: {r=}')
        #
        # elif isinstance(db, LessonPostgreSqlGino):
        #
        #     postgres_uri = f"postgresql://{secrets.db.user}:" \
        #                    f"{secrets.db.password}" \
        #                    f"@{secrets.db.host}:" \
        #                    f"{secrets.db.port}/" \
        #                    f"{secrets.db.name}"
        #
        #     await gino_db.set_bind(postgres_uri)
        #     await gino_db.gino.drop_all()
        #     await gino_db.gino.create_all()
        #
        #     await db.add_user(1, "One", "email")
        #     await db.add_user(2, "Two", "email@sszc")
        #     await db.add_user(3, "The", "email@mail")
        #     await db.add_user(4, "For", "email@email")
        #     await db.add_user(5, "FVVV", "email@gmail")
        #     await db.add_user(6, "SSSSS", "email@hotmail")
        #
        #     users = await db.select_all_users()
        #     mlog.info(f'{users=}')
        #
        #     user = await db.select_user(5)
        #     mlog.info(f'{user=}')
        #
        #     count = await db.count_users()
        #     mlog.info(f'{count=}')
        #
        #     mlog.info(f'--------------------------\n'
        #               f'created PSQL GINO\n'
        #               f'-----------------------')
        #
        # elif isinstance(db, LessonDjangoORM):
        #     user = await db.add_user(user_id=1231,
        #                              full_name='test_full',
        #                              username='test_user'
        #                              )
        #     mlog.info(f'{user=}')
        #     count = await db.count_users()
        #     mlog.info(f'{count=}')
        #
        #     user = await db.select_user(user_id=1231)
        #
        #     mlog.info(f'select_user: {user=}')
        #
        #     users = await db.select_all_users()
        #     mlog.info(f'all_users: {users=}')
        # elif isinstance(db, Task5DjangoORM):
        #
        #     await asyncio.sleep(0)
        #     #await create_default_items(self)

    async def _append_handler_zdefault(self):

        # @rate_limit(1, key='default')
        # @self.message_handler(commands=['helpfzvz'])
        # async def cmd_help(m: types.Message, chat: LessonChatModel):
        #
        #     await m.reply(
        #         f'Hello. This bot use default template.'
        #     )

        return
        # @self.errors_handler(exception=exceptions.MessageNotModified)
        # async def message_not_modified_handler(update, error):
        #     return True
        #     # errors_handler must return True if error was handled correctly

    async def aextra(self):

        for key in dir(self):
            if '_append_handler_' in key:

                handler_name = '_'.join(key.split('_')[3:])
                if handler_name not in self.handlers_to_register:
                    method = getattr(self, key)

                    mlog.info(f'load handler: {handler_name}: {method}')
                    await method()
                    self.handlers_to_register.add(handler_name)
                else:
                    mlog.info(f'duplicate handler: {handler_name}')
