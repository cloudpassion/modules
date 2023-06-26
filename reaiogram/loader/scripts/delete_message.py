import asyncio

from asgiref.sync import sync_to_async, async_to_sync

from reaiogram.default.bot import Bot
from reaiogram.dispatcher import Dispatcher
from reaiogram.types.django import TorrentFile, TorrentPiece, TgMessage

from config import secrets
from log import logger


async def delete_messages(dp: Dispatcher, bot: Bot):
    run = input('run delete message??, type " start " for run')
    if run and run == 'start':
        asyncio.create_task(_delete_messages(dp, bot))


async def _delete_messages(dp: Dispatcher, bot: Bot):

    torrents = TorrentFile.objects.all()
    # for torrent in torrents:
    #     logger.info(f'{torrent=}')
    #
    messages = TgMessage.objects.all()
    for message in messages:

        if message.deleted:
            continue

        if message.thread_id in (247, 3910):
            logger.info(f'{message=}')

            while True:
                try:
                    await bot.delete_message(
                        secrets.bt.chat.pieces.id, message_id=message.id
                    )
                    message.deleted = True
                    await sync_to_async(message.save)()
                    # await asyncio.sleep(1)
                    break
                except Exception as exc:

                    logger.info(f'{exc=}')
                    if 'message to delete not found' in f'{exc}':
                        message.deleted = True
                        await sync_to_async(message.save)()
                        break
                    if "message can't be deleted" in f'{exc}':
                        break

                    await asyncio.sleep(20)

                await asyncio.sleep(1)
