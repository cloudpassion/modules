import re
from typing import Union

from aiogram.dispatcher.filters import Regexp, Command, CommandStart
from aiogram.utils import exceptions
from aiogram import types
from aiogram.types.chat_member import ChatMemberStatus

from reaiogram.dispatcher.default import Dispatcher
#from reaiogram.db.schemas import Task5DjangoORM
from reaiogram.filters import NotRegisteredFilter

from log import logger


async def check_user(msg: types.Message, dispatcher: Dispatcher):

    try:
        sql_user = await dispatcher.sql.select_user(user_id=msg.from_user.id)
    except Exception:
        logger.debug(f'no user in database with user_id={msg.from_user.id}')
        return

    return sql_user


class Task5Handler(Dispatcher):

    async def _append_handler_lesson_inline(self):

        @self.inline_handler()
        async def task5_default_inline_handler(query: types.InlineQuery):

            results = []
            check = await check_user(query, self)
            query_text = query.query
            if check:
                if len(query_text) <= 2:
                    results.append(
                        types.InlineQueryResultArticle(
                            id="help",
                            title="Write more 2 letters for search items",
                            input_message_content=types.InputMessageContent(
                                message_text="If no words. Get all items. You can write more 2 words "
                                             "for search",
                            ),
                            reply_markup=types.InlineKeyboardMarkup(
                                row_width=2, inline_keyboard=[[
                                    types.InlineKeyboardButton(
                                        text='Continue search',
                                        switch_inline_query_current_chat='',
                                    )
                                ]]
                            )
                        ),
                    )

                    items = await self.sql.get_items()
                    new_items = []
                    for item in items:
                        if re.search('^[.? ]?', item.title):
                            continue

                        new_items.append(item)
                else:
                    items = []
                    items_title = await self.sql.search_items('title', query_text)
                    items_desc = await self.sql.search_items('description', query_text)
                    for i in range(0, 25):
                        try:
                            if not items_title[i] in items:
                                items.append(items_title[i])
                        except IndexError:
                            pass
                        try:
                            if not items_desc[i] in items:
                                items.append(items_desc[i])
                        except IndexError:
                            pass

                logger.info(f'{items=}')
                logger.info(f'{results=}')
                results.extend([
                    types.InlineQueryResultArticle(
                        id=item.id,
                        title=f'|{item.title}',
                        description=item.description,
                        input_message_content=types.InputMessageContent(
                            message_text='item'
                        ),
                        reply_markup=None,
                        thumb_url=item.thumb_image_url,
                        thumb_width=128,
                        thumb_height=64,

                    ) for item in items[0:49]],
                )

                if len(results) < 1:
                    results.append(
                        types.InlineQueryResultArticle(
                            id="no_results",
                            title="No items. Type something else",
                            input_message_content=types.InputMessageContent(
                                message_text=f'No items based on {query_text}',
                            )
                        )
                    )
            else:
                results.append(
                    types.InlineQueryResultArticle(
                        id='no_allowed',
                        title='Hi, you not registetered for search items '
                              f'join in bot with refferal key or go to '
                              f'bot private chat for get more info',
                        input_message_content=types.InputMessageContent(
                            message_text=f'To bot via link for additional info '
                                         f'https://t.me/{(await self.bot.me).username}?start=help'
                        ),
                    )
                )

            await query.answer(
                results=results,
                cache_time=5,
            )

        @self.message_handler(NotRegisteredFilter())
        async def no_registered_help(in_data: Union[types.Message, types.CallbackQuery]):

            logger.debug('this1')

            if isinstance(in_data, types.Message):
                text = in_data.text
            else:
                logger.debug(f'hmm: {in_data=}')
                return

            await in_data.bot.send_message(
                chat_id=in_data.chat.id,
                text='Hi. Your not registered. '
                     'For register your need join to bot '
                     'with referral key gain from exist user. '
                     'If your don\'t have friends your can join '
                     f'in channel '
                     f'https://t.me/{(await self.bot.me).username.replace("bot","cha")} '
                     'and send some text here again or click to "Refresh Access"\n\n'
                     'And if you can referral key and bot does not recognise your enter it '
                     'again please by click on "Enter Key" button. Thanks. See you later',
                reply_markup=types.InlineKeyboardMarkup(
                    row_width=2,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text='Enter Key',
                                callback_data='enter_referral_key'
                            ),
                            types.InlineKeyboardButton(
                                text='Refresh Access',
                                callback_data='refresh_access'
                            )
                        ]
                    ]
                )
            )

        @self.message_handler(NotRegisteredFilter())
        @self.callback_query_handler()


        @self.message_handler(commands=['menu'])
        async def menu_command(msg: types.Message, **kwargs):

            if not await check_user(msg, self):
                return

            await msg.answer(
                text='Inline main menu',
                reply_markup=types.InlineKeyboardMarkup(
                    row_width=2,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text='Select item',
                                switch_inline_query_current_chat=''
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text='Referral info',
                                callback_data='referral_info',
                            )
                        ]
                    ]
                )
            )
