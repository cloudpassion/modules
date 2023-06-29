import asyncio

from aiogram.types.message import Message

from config import secrets
from log import logger

from ....default.bot import Bot
from ....dispatcher import Dispatcher
from ....django_telegram.django_telegram.datamanager.models import (
    TorrentFile as DjangoTorrentFile,
    TorrentPiece as DjangoTorrentPiece,

    TgChat, TgMessage, TgUser
)
from ....types.torrent.torrent import TorrentFile
from ....types.torrent.status import TorrentStatus
from ....types.tg.message import MergedTelegramMessage


async def continue_torrent_downloading(dp: Dispatcher, bot: Bot):

    torrents = DjangoTorrentFile.objects.all()
    logger.info(f'{torrents}')

    to_download = []
    for dj_torrent in torrents:

        if dj_torrent.info_hash in (
                '3f6cca286969bd029d6096023bc90fc3fdbc2eae',
                '34af699d199c4b87d0602796acdf05a94975dabf',
                '63d0151a5a6140ced94cb6adda7502821a005158',
                'b3c10f038bc62b5231bae779578646c6e110839a',
                'a31d032ee7454a3620c1b02ded773a9e6734afd6',
                'b851474b74f65cd19f981c723590e3e520242b97',
        ):
            continue

        pieces = DjangoTorrentPiece.objects.filter(torrent=dj_torrent).all()

        count_pieces = len(pieces)
        if not count_pieces:
            to_download.append(dj_torrent)
            continue

        for piece in pieces:
            if not piece.message or not piece.length:
                # logger.info(f'{piece.message=}')
                # logger.info(f'{piece.length=}')
                # logger.info(f'add {dj_torrent.name}\n{dj_torrent.info_hash}')
                to_download.append(dj_torrent)
                break

    [logger.info(f'{x.name}\n') for x in to_download]

    for dwn in to_download:

        if dwn.message:
            message = await bot.forward_message(
                chat_id=secrets.bt.chat.trash.id,
                from_chat_id=dwn.message.chat.id,
                message_id=dwn.message.id,
            )
            # logger.info(f'{message=}')

            old_kwargs = {}

            for mu in TgMessage.db_keys:
                if not hasattr(message, mu):
                    continue

                old_kwargs.update({
                    mu: getattr(message, mu)
                })
                # setattr(old_message, mu, getattr(message, mu))
            old_kwargs['chat'] = {}
            old_kwargs['from_user'] = {}

            old_kwargs.update({
                'date': message.forward_date,
                'message_id': dwn.message.id,
                'thread_id': dwn.message.thread_id
            })

            for cu in TgChat.db_keys:
                try:
                    getattr(dwn.message.chat, cu)
                except AttributeError:
                    continue

                old_kwargs['chat'].update({
                    cu: getattr(dwn.message.chat, cu)
                })

            for fu in TgUser.db_keys:
                try:
                    getattr(dwn.message.from_user, fu)
                except AttributeError:
                    continue

                old_kwargs['from_user'].update({
                    fu: getattr(dwn.message.from_user, fu)
                })

            # logger.info(f'{old_kwargs=}')

            old_message = Message(**old_kwargs)

            merged_message = MergedTelegramMessage(
                dp.orm, old_message
            )
            #
            await merged_message.merge_message()

        else:
            merged_message = None

        torrent = TorrentFile(
            dp=dp,
            orm=dp.orm, bot=bot,
            merged_message=merged_message,
        )

        await torrent.download_torrent_from_tg(
            file_id=dwn.message.document.file_id
        )
        torrent_status = TorrentStatus()
        dp.torrents[torrent.info_hash] = torrent_status

        torrent_status.in_work = True
        #wait torrent.save_to_django()

        await torrent.add_pieces_to_django()

        asyncio.create_task(
            torrent.download_some_pieces(version=6)
        )

        # break
