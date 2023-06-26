import gc
import os
import re
import asyncio
import random
import time
import psutil
import tracemalloc

from typing import BinaryIO
from pathlib import Path
from io import BytesIO
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import BufferedInputFile, InputFile

from atiny.reos.dir.create import create_dir
from config import secrets, settings
from log import logger, log_stack

from bt.encoding.stuff import from_hex_to_bytes, from_bytes_to_hex

from reaiogram.types.torrent.default import DefaultTorrent, AbstractMergedTelegram
from bt.torrent import TorrentPiece

from ....types.django import (
    TorrentPiece as DjangoTorrentPiece,
    TgDocument as DjangoTgDocument,
    TgMessage as DjangoTgMessage,
)

from telethon import TelegramClient, events
from telethon.utils import resolve_bot_file_id
# from telethon.tl.custom.file import F

from tg_file_id.file_id import FileId
from tg_file_id.file_unique_id import FileUniqueId

TG_CHAT_ID = secrets.bt.download.chat_id
TG_API_ID = secrets.bt.download.api_id
TG_API_HASH = secrets.bt.download.api_hash


async def new_client(client):

    try:
        await client.disconnect()
    except:
        pass

    try:
        await client.close()
    except:
        pass

    client = TelegramClient(
        '.tg_download_session', TG_API_ID, TG_API_HASH,
        auto_reconnect=False
    )
    await client.start()
    return client


class TorrentGrabVersion5(
    DefaultTorrent,
    AbstractMergedTelegram
):

    async def grab_torrent_from_telegram_version5(
            self,
            out_dir,
            version=5
    ):

        create_dir(out_dir)
        # messages = DjangoTgMessage.objects.filter(caption=)
        dj_documents = DjangoTgDocument.objects.all()
        documents = [
            x for x in dj_documents if (
                    'txt' in x.file_name
            ) and self.info_hash in x.file_name
        ]
        #
        # logger.info(f'{len(documents)}')

        all_messages = DjangoTgMessage.objects.filter().all()

        # cache variant
        # with open('.txt_ids', 'r') as ir:
        #     ids = [int(x.splitlines()[0]) for x in ir.readlines()]
        #
        # txt_messages = [
        #     m for m in all_messages if m.id in ids
        # ]
        # life variant
        txt_messages = [
            m for m in all_messages if m.document in documents
        ]
        # with open('.ids', 'w') as w:
        #     w.writelines([f'{m.id}\n' for m in txt_messages])

        logger.info(f'{len(txt_messages)=}')

        dj_pieces = DjangoTorrentPiece.objects.filter(
            torrent=await self.from_orm(),
        )
        logger.info(f'{len(dj_pieces)}')

        async def get_txt_files(
            _documents, count
        ):
            files = []
            for document in _documents:

                file_id = document.file_id
                file_name = document.file_name

                while True:
                    try:
                        # logger.info(f'download txt {file_id=}')
                        txt_data = await self.bot.download(
                            file=file_id,
                        )
                        break
                    except Exception as exc:
                        logger.info(f'{exc=}')
                        await asyncio.sleep(20)

                files.append([file_name, txt_data])
                if count and len(files) > count:
                    break

            return files

        all_txt_bytes = [
            [
                name, data
            ] for name, data in await get_txt_files(
                [f.document for f in txt_messages], None
            )
        ]

        async def merge_some(txt_bytes, rebuild_tree=True):

            client = None

            file_bytes = {}
            for txt in txt_bytes:
                txt_file, txt_bt = txt

                info_hash = txt_file.split('_')[1].split('.')[0]

                dj_piece = [
                    x for x in dj_pieces if (
                            info_hash in x.info_hash
                    )][0]

                tmp_path = f'.data_tmp/{info_hash}'
                # if os.path.isfile(f'.data_tmp/{info_hash}'):
                #     continue

                document = dj_piece.message.document

                if os.path.isfile(tmp_path) and os.stat(tmp_path).st_size != 0:
                    with open(tmp_path, 'rb') as f:
                        file_data = BytesIO(f.read())

                    file_bytes[txt_file] = file_data
                    continue

                size = document.file_size
                if size <= 20971520:
                    file_bytes[txt_file] = await self.bot.download(
                        document.file_id
                    )

                    with open(tmp_path, 'wb') as f:
                        f.write(file_bytes[txt_file].read())

                    file_bytes[txt_file].seek(0)
                else:

                    async def sleep_send(file_id):
                        # await asyncio.sleep(2)
                        await self.bot.send_document(
                            TG_CHAT_ID, file_id, caption=info_hash
                        )

                    if not client:
                        client = await new_client(None)

                    # asyncio.create_task(
                    await sleep_send(document.file_id)
                    # )
                    await asyncio.sleep(2)

                    del_ids = []

                    while True:
                        try:
                            messages = await client.get_messages((await self.bot.me()).id)
                            break
                        except Exception as exc:
                            logger.info(f'{exc=}')
                            client = await new_client(client)
                            continue

                    while True:
                        try:
                            msg = messages.pop()
                            await asyncio.sleep(0)
                        except IndexError:
                            try:
                                messages = await client.get_messages((await self.bot.me()).id)
                                break
                            except Exception as exc:
                                logger.info(f'{exc=}')
                                client = await new_client(client)

                            continue

                        # logger.info(f'{msg=}\n{dir(msg)=}')
                        # await asyncio.sleep(2)
                        # if not hasattr(msg, 'caption'):
                        #     del_ids.append(msg.id)
                        #     await asyncio.sleep(1)
                        #     continue

                        if not msg.message:
                            del_ids.append(msg.id)
                            continue

                        if info_hash not in msg.message:
                            del_ids.append(msg.id)
                            continue

                        # file_data = ()
                        while True:
                            try:
                                # file_data = BinaryIO()
                                blob = await client.download_media(
                                    msg, file=bytes
                                )
                                # logger.info(f'{file_data=}')
                                # logger.info(f'{blob=}')
                                file_data = BytesIO(blob)
                                # file_data.read()
                                # file_data.seek(0)
                                break
                            except Exception as exc:

                                # await client.close()
                                client = new_client(client)
                                logger.info(f'{exc}')
                                await asyncio.sleep(20)

                        with open(tmp_path, 'wb') as f:
                            f.write(file_data.read())

                        file_data.seek(0)
                        break

                    try:
                        await client.delete_messages(TG_CHAT_ID, del_ids)
                    except Exception as exc:
                        logger.info(f'{exc=}')
                        client = new_client(client)
                        logger.info(f'{exc}')
                        await asyncio.sleep(20)

                    file_bytes[txt_file] = file_data

            # logger.info(f'{file_bytes=}')

            self.merge_pieces(
                out_dir,
                merge_from='bytes',
                metadata_from='bytes',
                version=version,
                txt_bytes=txt_bytes,
                file_bytes=file_bytes,
                rebuild_tree=rebuild_tree,
            )

            if client:
                try:
                    await client.disconnect()
                except Exception as exc:
                    logger.info(f'{exc=}')
                try:
                    await client.close()
                except Exception as exc:
                    logger.info(f'{exc=}')

            # merge_some end

        new_tree = True
        while all_txt_bytes:

            some_txt_bytes = all_txt_bytes[:10]
            await merge_some(some_txt_bytes, rebuild_tree=new_tree)
            new_tree = False
            # for info, some in some_txt_bytes:
            #     Path(f'.data_tmp/{info}').touch()

            all_txt_bytes = all_txt_bytes[10:]

        # txt_bytes = [[file_name1, bytes_from_this_file], ...]
        # file_bytes = {file_name1: data_file_bytes], ...}

