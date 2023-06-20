# from operator import itemgetter
#
# from aiogram.dispatcher.filters.state import StatesGroup, State
# from aiogram.types import Message, CallbackQuery
#
# from aiogram_dialog import (
#     Dialog, DialogManager, DialogRegistry, Window, StartMode, BaseDialogManager
# )
# from aiogram_dialog.widgets.input import MessageInput
# from aiogram_dialog.widgets.kbd import (
#     Button, Group, Next, Back, Cancel, Checkbox, Row, Radio, Multiselect, Select
# )
# from aiogram_dialog.widgets.text import Const, Format, Progress
#
#
#
# class Register(StatesGroup):
#     settings = State()
#
#
# extra_settings = Dialog(
#     Window(
#         Back(Const("Back")),
#         state=Register.extra_settings
#     )
# )
# settings_dialog = Dialog(
#     Window(
#         Const("Global Settings"),
#         Radio(
#             Format("🔘 {item[0]}"), Format("◯ {item[0]}"),
#             "radio",
#             itemgetter(0),
#             (
#                 ("Global Overrida", 1), ("Extra Settings", 2), ("Silent", 3),
#             )),
#         Radio(
#             Format("🔘 {item[0]}"), Format("◯ {item[0]}"),
#             "radio",
#             itemgetter(0),
#             (
#                 ("Video", 1), ("Audio", 2), ("Gif", 3), ("Images", 4),
#             )),
#         Radio(
#             Format("🔘 {item[0]}"), Format("◯ {item[0]}"),
#             "radio",
#             itemgetter(0),
#             (
#                 ("Album", 5), ("Text", 6), ("Text Format", 7), ("Caption Format", 8),
#             )),
#
#         Radio(
#             Format("🔘 {item[0]}"), Format("◯ {item[0]}"),
#             "radio",
#             itemgetter(0),
#             (
#                 ("Add Item", 9), ("Items", 10), ("Del Item", 11)
#             )),
#         state=Register.settings
#     ),
# )
#
#
# def register_settings_dialog(dp, registry: DialogRegistry):
#     registry.register(settings_dialog)
#     registry.register(extra_settings)