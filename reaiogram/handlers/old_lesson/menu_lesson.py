import random
import time

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler

from log import mlog, log_stack
from reaiogram.dispatcher.default import Dispatcher
from reaiogram.keyboards import (
    lesson_menu_first, lesson_menu_choise, buy_callback, lesson_menu_pear,
    lesson_menu21,
    menu22_item_callback, menu22_item_rate_callback
)


class LessonMenuHandler(Dispatcher):

    async def _append_handler_lesson_menu1(self):

        @self.message_handler(commands=['menuz'])
        async def cmd_lesson_menu1(msg: types.Message):
            await msg.reply("Chose your destiny", reply_markup=lesson_menu_choise)

        @self.message_handler(text="Row2Button2")
        async def row2button2(msg: types.Message):
            await msg.reply(text="remove", reply_markup=types.ReplyKeyboardRemove())

        @self.callback_query_handler(buy_callback.filter(item_name="pear"))
        async def buy_pear(call: types.CallbackQuery, callback_data: dict):
            mlog.info(f'----------------c {call.data=}')
            mlog.info(f'----------------d {callback_data=}')
            quantity = callback_data.get("quantity")
            await call.message.answer(
                text=f"you buy: pear with count: {quantity}",
                reply_markup=lesson_menu_pear,
            )

    async def _append_handler_lesson_menu21(self):

        @self.message_handler(commands=['inline_buttons_1'])
        async def cmd_lesson_menu21(msg: types.Message):
            await msg.answer(f'Edit @Sberleadbot info.\n\n'
                             f'Name: Бот для Заданий на Курсе Udemy\n'
                             f'Description: ?\ggn'
                             f'About: ?\n'
                             f'Botpic: ? no botpic\n'
                             f'Commands: no commands yet\n',
                             reply_markup=lesson_menu21)

    async def _append_handler_lesson_menu22(self):
        from random_word import RandomWords
        self.menu22_items = {}
        self.menu22_except_items = [
            ['Кекс', 'https://images.unsplash.com/photo-1594001222400-0d0d7a64183a?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=400&ixid=MnwxfDB8MXxyYW5kb218MHx80LrQtdC60YEsX19jYWNoZUJ1c3Rlcnx8fHx8fDE2MjY3NDQwMTk&ixlib=rb-1.2.1&q=80&w=600'],
            ['Пирог', 'https://images.unsplash.com/photo-1605736177485-525f3377f9a1?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=400&ixid=MnwxfDB8MXxyYW5kb218MHx80J_QuNGA0L7QsyxfX2NhY2hlQnVzdGVyfHx8fHx8MTYyNjc0NDEyNw&ixlib=rb-1.2.1&q=80&w=600']
        ]
        self.rnd_word = RandomWords()

        _top = '👍'
        _bad = '👎'
        _top_data = '+'
        _bad_data = '-'

        @self.message_handler(commands=['items'])
        async def cmd_lesson_menu22(msg: types.Message):
            random_id = lambda x: random.randint(111111, 222222)
            _items = [random_id(1), random_id(2)]
            i = 0
            for item_id in _items:

                self.menu22_items.update(
                    {
                        item_id: {_top: 0, _bad: 0}
                    }
                )

                try:
                    item_name = self.rnd_word.get_random_word()
                    item_url = f'https://source.unsplash.com/600x400/?{item_name}' \
                               f'=&__cacheBuster={time.strftime("%s")}'
                except:
                    log_stack.info(f'name,url')
                    item_name = self.menu22_except_items[_items.index(item_id)][0]
                    item_url = self.menu22_except_items[_items.index(item_id)][1]

                lesson_menu22_item = types.InlineKeyboardMarkup()
                lesson_menu22_item.insert(
                    types.InlineKeyboardButton(
                        text='Купить Товар',
                        callback_data=menu22_item_callback.new(
                            item_id=item_id, operation="buy"
                        ))
                )
                lesson_menu22_item.row(
                    types.InlineKeyboardButton(
                        text=_top,
                        callback_data=menu22_item_rate_callback.new(
                            rate=_top_data, item_id=item_id,
                        )),
                    types.InlineKeyboardButton(
                        text=_bad,
                        callback_data=menu22_item_rate_callback.new(
                            rate=_bad_data, item_id=item_id,
                        ))
                )
                lesson_menu22_item.row(
                    types.InlineKeyboardButton(
                        text='Поделиться с другом',
                        switch_inline_query=f'{item_id}'
                    )
                )

                await self.bot.send_photo(
                    chat_id=msg.chat.id,
                    caption=item_name.capitalize(),
                    photo=item_url,
                    reply_markup=lesson_menu22_item
                )

        @self.callback_query_handler(menu22_item_callback.filter(operation="buy"))
        async def menu22_item_buy(query: types.CallbackQuery, callback_data: dict):
            item_id = callback_data.get('item_id')
            await query.message.edit_caption(
                caption=f'Покупай товар номер {item_id}!'
            )
            raise CancelHandler()

        @self.callback_query_handler(menu22_item_rate_callback.filter(rate=_top_data))
        async def menu22_item_top(query: types.CallbackQuery, callback_data: dict):
            await query.answer(
                text='Тебе понравился этот товар'
            )
            raise CancelHandler()

        @self.callback_query_handler(menu22_item_rate_callback.filter(rate=_bad_data))
        async def menu22_item_bad(query: types.CallbackQuery, callback_data: dict):
            await query.answer(
                text='Тебе не понравился этот товар'
            )
            raise CancelHandler()