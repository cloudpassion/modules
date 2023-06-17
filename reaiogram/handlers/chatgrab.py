from io import BytesIO
from aiogram.utils import exceptions
from aiogram import types
from aiogram.types.chat_member import ChatMemberStatus

from reaiogram.dispatcher.default import Dispatcher
from log import mlog, log_stack


class ChatGrabHandler(Dispatcher):

    async def _append_handler_chatgrab(self):

        @self.message_handler(content_types=types.ContentType.AUDIO)
        @self.message_handler(content_types=types.ContentType.VOICE)
        @self.message_handler(content_types=types.ContentType.DOCUMENT)
        async def chat_grab(msg: types.Message):
            mlog.info(f'm: {msg}')
            doc = msg.audio if msg.audio else msg.voice if msg.voice else msg.document

            # save_to_io = BytesIO()

            # shazam
            # await doc.download(destination=save_to_io)
            #
            #
            # shazam = Shazam()
            # out = await shazam.recognize_song(save_to_io)
            # await msg.reply(f'{out=}')
            # #await msg.answer_audio(types.InputFile(path_or_bytesio=save_to_io))


