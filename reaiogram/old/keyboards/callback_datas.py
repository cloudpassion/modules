from aiogram.utils.callback_data import CallbackData

buy_callback = CallbackData("buy", "item_name", "quantity")

menu21_callback = CallbackData("edit", "option")

menu22_item_callback = CallbackData("item", "operation", "item_id")
menu22_item_rate_callback = CallbackData("item", "rate", "item_id")


task5_not_register = CallbackData("what")
