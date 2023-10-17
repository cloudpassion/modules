import asyncio
from typing import Dict, Any, Callable, Awaitable

from aiogram.types import Message, Update
from aiogram.dispatcher.event.bases import SkipHandler

from reaiogram.default.router import Router
from reaiogram.utils.enums import MESSAGE_UPDATE_TYPES

from config import secrets
from log import logger

# from ....dispatcher.default import ExtraDispatcher

from reaiogram.types.tg.message import MergedTelegramMessage
from reaiogram.types.torrent.torrent import TorrentFile, TorrentPiece

from ....types.torrent.status import TorrentStatus


# class TorrentRouter(
#     ExtraDispatcher
# ):
#
#     async def _append_handler_torrent_to_orm_0(self):
#
#         @self.update.outer_middleware()

async def parse_message_for_torrents(
        handler: Callable[[Update, Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
) -> Any:

    document = message.document
    if not document:
        return await handler(message, data)

    if document.mime_type != 'application/x-bittorrent':
        return await handler(message, data)

    merged_message = data['merged_message'] or data['merged_edited_message']
    bot = data['bot']

    dp = bot.dp

    torrent = TorrentFile(
        dp=dp,
        orm=dp.orm, bot=bot,
        merged_message=merged_message,
    )

    await torrent.download_torrent_from_tg()

    logger.info(f'{torrent.info_hash=}')

    if torrent.info_hash in (
            '3f6cca286969bd029d6096023bc90fc3fdbc2eae',
            '34af699d199c4b87d0602796acdf05a94975dabf',
            '63d0151a5a6140ced94cb6adda7502821a005158',
            'b3c10f038bc62b5231bae779578646c6e110839a',
            'a31d032ee7454a3620c1b02ded773a9e6734afd6',
            'b851474b74f65cd19f981c723590e3e520242b97',
    ):
        logger.info(f'skip old')
        return

    if torrent.info_hash in secrets.temp.skip:
        logger.info(f'{torrent.name} in skip')
        return

    try:
        torrent_status = dp.torrents[torrent.info_hash]
    except KeyError:
        torrent_status = TorrentStatus()
        dp.torrents[torrent.info_hash] = torrent_status

    if torrent_status.in_work:
        logger.info(f'skip {torrent.info_hash}, already in queue')
        try:
            await message.reply(
                text=f'{torrent.name}\n'
                     f'{torrent.comment}\n'
                     f'{torrent.publisher_url}\n'
                     f'{torrent.info_hash}\n'
                     f'already in queue'
            )
        except Exception:
            pass
        return await handler(message, data)

    torrent_status.in_work = True

    logger.info(f'{torrent=}')
    await torrent.save_to_django()
    await torrent.add_pieces_to_django()

    data['torrent'] = torrent

    torrent_status.set_torrent(torrent)
    torrent_status.in_work = False

    return await handler(message, data)


def register_torrent_file_prepare(router: Router):

    for msg_type in MESSAGE_UPDATE_TYPES:
        logger.info(f'msg:{msg_type=}')
        router_msg = getattr(router, msg_type)
        router_msg.outer_middleware.register(parse_message_for_torrents)

    # router.message.outer_middleware.register(parse_message_for_torrents)
    # router.edited_message.outer_middleware.register(parse_message_for_torrents)
    #
    # router.channel_post.outer_middleware.register(parse_message_for_torrents)
    # router.edited_channel_post.outer_middleware.register(parse_message_for_torrents)



