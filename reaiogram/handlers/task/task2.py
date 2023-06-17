from aiogram import types
from aiogram.dispatcher import FSMContext

from reaiogram.dispatcher.default import Dispatcher
from reaiogram.states import Task2States


class Task2Handler(Dispatcher):

    async def _append_handler_task2(self):

        @self.message_handler(commands=['form'])
        async def cmd_form(m: types.Message, state: FSMContext):

            await Task2States.Q1.set()
            await m.reply('Уважаемый UserBot, напишите свое Имя')

        @self.message_handler(state=Task2States.Q1)
        async def cmd_form_q1(m: types.Message, state: FSMContext):

            async with state.proxy() as data:
                data["name"] = m.text

            await Task2States.Q2.set()
            await m.reply('Уважаемый UserBot, напишите свой Email')

        @self.message_handler(state=Task2States.Q2)
        async def cmd_form_q2(m: types.Message, state: FSMContext):

            async with state.proxy() as data:
                data["email"] = m.text

            await Task2States.Q3.set()
            await m.reply('Уважаемый UserBot, напишите свой Номер телефона')

        @self.message_handler(state=Task2States.Q3)
        async def cmd_form_q3(m: types.Message, state: FSMContext):

            async with state.proxy() as data:
                data["phone"] = m.text

            data = await state.get_data()

            name = data["name"]
            email = data["email"]
            phone = data["phone"]

            await m.answer(f'Привет! Ты ввел следующие данные:\n\n' \
                           f'Имя - {name}\n\n' \
                           f'Email - {email}\n\n' \
                           f'Телефон: - {phone}')

            await state.finish()

