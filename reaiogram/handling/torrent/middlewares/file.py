import asyncio
from typing import Dict, Any, Callable, Awaitable

from aiogram.types import Message, Update
from aiogram.dispatcher.event.bases import SkipHandler

from reaiogram.default.router import Router
from reaiogram.utils.enums import MESSAGE_UPDATE_TYPES

from log import logger

# from ....dispatcher.default import ExtraDispatcher

from reaiogram.types.tg.message import MergedTelegramMessage
from reaiogram.types.torrent.torrent import TorrentFile, TorrentPiece


# class TorrentRouter(
#     ExtraDispatcher
# ):
#
#     async def _append_handler_torrent_to_orm_0(self):
#
#         @self.update.outer_middleware()

async def parse_message_for_torrents(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
) -> Any:
    document = message.document
    if not document:
        return await handler(message, data)

    if document.mime_type != 'application/x-bittorrent':
        return await handler(message, data)

    merged_message = data['merged_message']
    bot = data['bot']

    dp = bot.dp

    torrent = TorrentFile(
        dp=dp,
        orm=dp.orm, bot=bot,
        merged_message=merged_message,
    )

    await torrent.download_torrent_from_tg()

    if dp.torrent.get(torrent.info_hash):
        logger.info(f'skip {torrent.info_hash}, now in queue')
        return await handler(message, data)

    dp.torrent[torrent.info_hash] = True
    data['torrent'] = torrent

    await torrent.save_to_django()
    await torrent.add_pieces_to_django()

    dp.torrent[torrent.info_hash] = False

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



