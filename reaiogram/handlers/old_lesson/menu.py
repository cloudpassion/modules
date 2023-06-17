from typing import Union

from reaiogram.dispatcher.default import Dispatcher

from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery, Message

from reaiogram.keyboards.inline.menu_keyboards import (
        menu_cd, categories_keyboard,
        subcategories_keyboard,
        items_keyboard, item_keyboard
    )


# Та самая функция, которая отдает категории. Она может принимать как CallbackQuery, так и Message
# Помимо этого, мы в нее можем отправить и другие параметры - category, subcategory, item_id,
# Поэтому ловим все остальное в **kwargs
async def list_categories(
        message: Union[CallbackQuery, Message], dispatcher,
        **kwargs):
    # Клавиатуру формируем с помощью следующей функции (где делается запрос в базу данных)
    markup = await categories_keyboard(dispatcher)

    # Проверяем, что за тип апдейта. Если Message - отправляем новое сообщение
    if isinstance(message, Message):
        await message.answer("Смотри, что у нас есть", reply_markup=markup)

    # Если CallbackQuery - изменяем это сообщение
    elif isinstance(message, CallbackQuery):
        call = message
        await call.message.edit_reply_markup(markup)


# Функция, которая отдает кнопки с подкатегориями, по выбранной пользователем категории
async def list_subcategories(
        callback: CallbackQuery, category, dispatcher,
        **kwargs):
    markup = await subcategories_keyboard(category, dispatcher)

    # Изменяем сообщение, и отправляем новые кнопки с подкатегориями
    await callback.message.edit_reply_markup(markup)


# Функция, которая отдает кнопки с Названием и ценой товара, по выбранной категории и подкатегории
async def list_items(
        callback: CallbackQuery, category, subcategory, dispatcher,
        **kwargs):
    markup = await items_keyboard(category, subcategory, dispatcher)

    # Изменяем сообщение, и отправляем новые кнопки с подкатегориями
    await callback.message.edit_text(text="Смотри, что у нас есть", reply_markup=markup)


# Функция, которая отдает уже кнопку Купить товар по выбранному товару
async def show_item(callback: CallbackQuery, category, subcategory, item_id, dispatcher):
    markup = item_keyboard(category, subcategory, item_id)

    # Берем запись о нашем товаре из базы данных
    item = await dispatcher.sql.get_item(item_id)
    text = f"Купи {item.name}"
    await callback.message.edit_text(text=text, reply_markup=markup)


class LessonUserMenuHandler(Dispatcher):

    async def _append_handler_usermenu(self):
        # Хендлер на команду /menu
        @self.message_handler(Command("menu"))
        async def show_menu(message: types.Message):
            # Выполним функцию, которая отправит пользователю кнопки с доступными категориями
            await list_categories(message, self)

        # Функция, которая обрабатывает ВСЕ нажатия на кнопки в этой менюшке
        @self.callback_query_handler(menu_cd.filter())
        async def navigate(call: CallbackQuery, callback_data: dict):
            """
            :param call: Тип объекта CallbackQuery, который прилетает в хендлер
            :param callback_data: Словарь с данными, которые хранятся в нажатой кнопке
            """

            # Получаем текущий уровень меню, который запросил пользователь
            current_level = callback_data.get("level")

            # Получаем категорию, которую выбрал пользователь (Передается всегда)
            category = callback_data.get("category")

            # Получаем подкатегорию, которую выбрал пользователь (Передается НЕ ВСЕГДА - может быть 0)
            subcategory = callback_data.get("subcategory")

            # Получаем айди товара, который выбрал пользователь (Передается НЕ ВСЕГДА - может быть 0)
            item_id = int(callback_data.get("item_id"))

            # Прописываем "уровни" в которых будут отправляться новые кнопки пользователю
            levels = {
                "0": list_categories,  # Отдаем категории
                "1": list_subcategories,  # Отдаем подкатегории
                "2": list_items,  # Отдаем товары
                "3": show_item  # Предлагаем купить товар
            }

            # Забираем нужную функцию для выбранного уровня
            current_level_function = levels[current_level]

            # Выполняем нужную функцию и передаем туда параметры, полученные из кнопки
            await current_level_function(
                call,
                category=category,
                subcategory=subcategory,
                item_id=item_id,
                dispatcher=self
            )
