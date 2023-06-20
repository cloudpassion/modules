from aiogram import types
from .callback_datas import buy_callback, \
    menu21_callback


lesson_menu_first = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text='FirstArgument')
        ],
        [
            types.KeyboardButton(text="Row2Button1"),
            types.KeyboardButton(text="Row2Button2")
        ],
    ],
    resize_keyboard=True
)

lesson_menu_choise = types.InlineKeyboardMarkup(
    row_width=2, inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="buy 1",
                callback_data=buy_callback.new(
                    item_name="pear",
                    quantity=1)
            ),
            types.InlineKeyboardButton(
                text="buy 2",
                callback_data="buy:2:5"
            )
        ],
        [
            types.InlineKeyboardButton(
                text="Cancel",
                callback_data="cancel"
            )
        ]
    ]
)

lesson_menu_pear = types.InlineKeyboardMarkup()
PEAR_LINK = "https://core.telegram.org/bots/api#replykeyboardmarkup"
lesson_pear_link = types.InlineKeyboardButton(text="buy here", url=PEAR_LINK)
lesson_menu_pear.insert(lesson_pear_link)


lesson_menu21 = types.InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text='Edit Name',
                                       callback_data=menu21_callback.new(option="name")),
            types.InlineKeyboardButton(text='Edit Description',
                                       callback_data=menu21_callback.new(option="description")
                                       )
        ],
        [
            types.InlineKeyboardButton(text='Edit About',
                                       callback_data=menu21_callback.new(option="about")),
            types.InlineKeyboardButton(text='Edit Botpic',
                                       callback_data=menu21_callback.new(option="botpic"))
        ],
        [
            types.InlineKeyboardButton(text='Edit Commands',
                                       callback_data=menu21_callback.new(option="commands")),
            types.InlineKeyboardButton(text='<<Back to Bot',
                                       callback_data=menu21_callback.new(option="back"))
        ]
    ]
)
