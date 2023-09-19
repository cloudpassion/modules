import asyncio
import random

from aiogram.types import BufferedInputFile
from aiogram.types.message import Message

from bt.encoding.stuff import from_hex_to_bytes

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

from ....db.functions import DbFunctions


async def continue_torrent_downloading(dp: Dispatcher, bot: Bot):

    # await bot.download(
    #     'BQACAgIAAx0EcZWc1wACOgxknBIx3r76vwo-TF_UVpzV36SOxwACVC0AAn2y4EjRjqRCQEigay8E',
    #     '59286e3d01243e6d01fa82d37e36be4030bf0354'
    # )
    # await bot.download(
    #     'BQACAgIAAx0EcZWc1wACXzpknV-VZMWmSP2OFiTvctRvOPjr5gACi0MAAo7s6UjYmDaND62iXi8E',
    #     '7b9c6609f2bee84a2d7618191e797c252aae8baf'
    # )
    # logger.info(f'return dwn')
    # return

    torrents = DjangoTorrentFile.objects.all()
    logger.info(f'{len(torrents)=}')

    to_download = []
    to_index = []
    to_count = []

    for dj_torrent in reversed(torrents):

        # if len(to_download) >= 2:
        #     break

        if dj_torrent.info_hash in (
                '3f6cca286969bd029d6096023bc90fc3fdbc2eae',
                '34af699d199c4b87d0602796acdf05a94975dabf',
                '63d0151a5a6140ced94cb6adda7502821a005158',
                'b3c10f038bc62b5231bae779578646c6e110839a',
                'a31d032ee7454a3620c1b02ded773a9e6734afd6',
                'b851474b74f65cd19f981c723590e3e520242b97',
        ):
            continue

        if dj_torrent.info_hash in (
            '4c149ff07560b61d9899358a1f058ddc4f130094'
        ):
            continue

        if dj_torrent.info_hash in (
                'a26f81d6f68d0a3257ebb4806556a461c60d643f',
                'bd26bb559223a1395a5254e2d020906cd2927f97',
                '295a4473dd9ed9cc9e8023cbc56e3ca7fab3177c',

        ):
            logger.info(f'long/some: {dj_torrent.name} skip')
            continue

        if dj_torrent.info_hash in secrets.temp.skip:
            logger.info(f'{dj_torrent.name} in skip')
            continue

        if dj_torrent.redown_skip:
            logger.info(f'rd: {dj_torrent.name} skip')
            continue

        # test
        # to_download.append(dj_torrent)
        # break

        pieces = DjangoTorrentPiece.objects.filter(torrent=dj_torrent).all()

        count_pieces = len(pieces)
        logger.info(f'{dj_torrent=}, {count_pieces=}')

        if not dj_torrent.count:
            to_count.append(dj_torrent)
            to_download.append(dj_torrent)
            continue

        if count_pieces != dj_torrent.count:
            # to_count.append(dj_torrent)
            to_download.append(dj_torrent)
            continue

        if not count_pieces:
            to_download.append(dj_torrent)
            continue

        for piece in pieces:

            try:
                int(piece.index)
            except (TypeError, AttributeError):
                to_index.append(dj_torrent)
                to_download.append(dj_torrent)
                break

            if not piece.message or not piece.length:
                # logger.info(f'{piece.message=}')
                # logger.info(f'{piece.length=}')
                # logger.info(f'add {dj_torrent.name}\n{dj_torrent.info_hash}')
                to_download.append(dj_torrent)
                break


        else:
            dj_torrent.redown_skip = True
            dj_torrent.save()

            # log here
            # while True:
            if True:
                try:
                    await bot.send_message(
                        chat_id=secrets.bt.chat.download.id,
                        message_thread_id=secrets.bt.chat.download.thread_id,
                        text=f'{dj_torrent.name}\n'
                             f'{dj_torrent.info_hash}\n\n'
                             f'complete'
                    )
                except Exception as exc:
                    logger.info(f'{exc=}')
                    await asyncio.sleep(random.randint(10,20))
                    # continue
                #
                # break


    # logger.info(f'{len(to_index)=}')
    # quit()
    [logger.info(f'{x.name}\n') for x in to_download]

    for dwn in to_download:

        if dwn.message:
            try:
                message = await bot.forward_message(
                    chat_id=secrets.bt.chat.trash.id,
                    from_chat_id=dwn.message.chat.id,
                    message_id=dwn.message.id,
                )
                if not message:
                    logger.info(f'res3 {dwn.info_hash}')
                    continue

            except Exception:
                logger.info(f'resend {dwn.info_hash}')
                continue
        else:

            logger.info(f'torrent no have message where we can download data')
            # mb need add variant with m2t
            continue

        old_kwargs = {}

        for mu in TgMessage.db_keys:
            if not hasattr(message, mu):
                continue

            old_kwargs.update({
                mu: getattr(message, mu)
            })
            # setattr(old_message, mu, getattr(message, mu))
        try:
            message.forward_date
        except Exception:
            logger.info(f'resend2 {dwn.info_hash}')
            continue

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
            orm=dp.orm,
            message=old_message,
            skip_orm=True
        )

        await merged_message.merge_message()

        torrent = TorrentFile(
            dp=dp,
            orm=dp.orm, bot=bot,
            merged_message=merged_message,
        )

        await torrent.download_torrent_from_tg(
            file_id=dwn.message.document.file_id
        )

        if dwn in to_count:
            dwn.count = torrent.count
            dwn.save()
            continue

        torrent_status = TorrentStatus()
        dp.torrents[torrent.info_hash] = torrent_status

        torrent_status.set_torrent(torrent)
        torrent_status.in_work = True
        #wait torrent.save_to_django()

        if dwn in to_index:
            logger.info(f'{len(to_index)=}')

            t = to_index.pop(to_index.index(dwn))

            dj_pieces = DjangoTorrentPiece.objects.filter(torrent=t)

            for dj_piece in dj_pieces:

                if dj_piece.index:
                    continue

                torrent_piece = [
                    p for p in torrent.metadata.pieces if (
                            p.hash == from_hex_to_bytes(dj_piece.info_hash)
                    )
                ][0]

                # for k in [*DjangoTorrentPiece.db_keys, 'db_hash']:
                #     logger.info(f'{k=}, {getattr(dj_piece, k)}')

                dp.orm.hash_strings['piece'] = DjangoTorrentPiece.db_keys
                dj_piece.index = torrent_piece.index
                dj_piece.db_hash = dp.orm.calc_hash(
                    DjangoTorrentPiece,
                    {
                        k: getattr(dj_piece, k) for k in DjangoTorrentPiece.db_keys
                    }

                )
                # for k in [*DjangoTorrentPiece.db_keys, 'db_hash']:
                #         logger.info(f'{k=}, {getattr(dj_piece, k)}')

                dj_piece.save()

        await torrent.add_pieces_to_django()

        asyncio.create_task(
            torrent.download_some_pieces(version=6)
        )

    logger.info(f'end torrent downloading continue')
