import sys
import select
import asyncio

from aiogram.types import BufferedInputFile, InputMediaDocument

from reaiogram.default.bot import Bot
from reaiogram.dispatcher import Dispatcher
from ...types.django import TgMessage

from config import secrets
from log import logger


async def edit_media(dp: Dispatcher, bot: Bot):

    timeout = 0
    logger.info(f'type " start_edit_media " without spaces and quotes '
                f'for run: {__name__}')
    i, _, _ = select.select([sys.stdin], [], [], timeout)

    if i:
        run = sys.stdin.readline().strip()
    else:
        run = None

    # run = input('run delete message??, type " start " for run')
    if run and run == 'start_edit_media':
        asyncio.create_task(_edit_media(dp, bot))


async def _edit_media(dp: Dispatcher, bot: Bot):
    logger.info(f'{edit_media} func, {dp=}, {bot=}')
    msg: TgMessage = TgMessage.objects.filter(id=6096, thread_id=3910).first()

    # await bot.download(
    #     'BQACAgIAAx0EcZWc1wACGI9kmZ6BKjnmhtCQeHamYDInc8b9TwACKTQAAslCyEixpmk1sO7unS8E',
    #     't.txt',
    # )
    # return
    # file_name = 'd2d1f554a229c60580702374502b71646247806c_3bf5498be98e33b6326f8f1.txt'
    # with open(file_name, 'rb') as f:
    #     data = f.read()
    #
    # input_file = BufferedInputFile(
    #     data,
    #     filename=f'{file_name}.txt'
    # )

    # message = await bot.send_document(
    #     chat_id=msg.chat.id,
    #     document=input_file,
    # )

    file_id = 'BQACAgIAAx0EcZWc1wACGI9kmZ6BKjnmhtCQeHamYDInc8b9TwACKTQAAslCyEixpmk1sO7unS8E'
    file_id = ''
    doc = InputMediaDocument(
        type='document',
        media=file_id,
        caption='d2d1f554a229c60580702374502b71646247806c',
    )

    logger.info(f'{doc=}')
    # media = InputFile(
    #     filename=message.document.file_id
    # )
    rsp = await bot.edit_message_media(
        media=doc,
        chat_id=msg.chat.id, message_id=msg.id,
    )
    logger.info(f'{rsp=}')
    return
