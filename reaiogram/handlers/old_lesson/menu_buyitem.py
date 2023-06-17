from aiogram import types
from aiogram.dispatcher import FSMContext
from asgiref.sync import sync_to_async

#from reaiogram.django_template.lesson.usersmanage.models import Purchase
#from reaiogram.keyboards.inline.menu_keyboards import buy_item
from reaiogram.dispatcher.default import Dispatcher


class LessonUserMenuBuyItemHandler(Dispatcher):

    async def _append_handler_lesson_menu_buy_item(self):

        @self.callback_query_handler(buy_item.filter())
        async def enter_buy(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
            item_id = callback_data.get('item_id')
            user = await self.sql.select_user(user_id=call.from_user.id)
            item = await self.sql.get_item(item_id)

            purchase = Purchase()
            purchase.buyer = user
            purchase.item_id = item
            purchase.receiver = call.from_user.full_name

            await state.update_data(purchase=purchase, item=item)

            await call.message.answer("Write count")
            await state.set_state("enter_quantity")

        @self.message_handler(state="enter_quantity")
        async def enter_quantity(msg: types.Message, state: FSMContext):
            try:
                quantity = int(msg.text)
            except ValueError:
                await msg.answer("Incorrect")
                return

            async with state.proxy() as data:

                #data["purchase"].quantity = quantity
                data["purchase"].amount = quantity * data["item"].price

            await msg.answer("Send phone number", reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[
                    types.KeyboardButton("Send phone", request_contact=True)
                ]], resize_keyboard=True
            ))

            await state.set_state("enter_phone")

        @self.message_handler(state="enter_phone", content_types=types.ContentType.CONTACT)
        async def enter_phone(msg: types.Message, state: FSMContext):
            phone_number = msg.contact.phone_number
            data = await state.get_data()
            purchase = data.get("purchase")
            purchase.phone_number = phone_number
            await sync_to_async(purchase.save)()
            await msg.answer("Created", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
