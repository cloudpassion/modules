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

    async def check_complete_for_grab5(self):

        logger.info(f'start check')

        redis_hashes = []
        missing_pieces = set(self.metadata.pieces)

        for torrent_piece in self.pieces:

            # continue

            dj: DjangoTorrentPiece = await torrent_piece.from_orm()

            # info_hash = torrent_piece.info_hash
            # i_h = f'{dj.index}_{info_hash}'

            # redis = self.redis.get(i_h)
            if dj.message:
                #or dj.resume_data or redis:
                # if redis:
                #     redis_hashes.append(i_h)

                item = [
                    p for p in missing_pieces if (
                            p.hash == from_hex_to_bytes(torrent_piece.info_hash) and p.index == torrent_piece.index
                    )
                ][0]
                # index = missing_pieces.index()
                # del missing_pieces[index]
                missing_pieces.remove(item)
                # logger.info(f'piece already downloaded')
                # continue

        return missing_pieces

    async def grab_torrent_from_telegram_version5(
            self,
            out_dir,
            version=5
    ):

        create_dir(out_dir)
        # messages = DjangoTgMessage.objects.filter(caption=)
        # dj_documents = DjangoTgDocument.objects.all()
        # documents = [
        #     x for x in dj_documents if (
        #             'txt' in x.file_name
        #     ) and self.info_hash in x.file_name
        # ]
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

        # all docs in db
        dj_documents = DjangoTgDocument.objects.all()

        # all pieces in db by torrent
        dj_pieces = DjangoTorrentPiece.objects.filter(
            torrent=await self.from_orm(),
            # version=6,
        )
        logger.info(f'{len(dj_pieces)=}')

        # docs name for txt message search
        # dji_docs_names = [
        #     x.message.document.file_name.split('.')[0] for x in dj_pieces
        # ]
        # txt docs
        # dji_txt_docs = []
        #
        # for dj_doc in dj_documents:
        #     if 'txt' not in dj_doc.file_name:
        #         continue
        #
        #     if dj_doc.file_name.split('.')[0] not in dji_docs_names:
        #         continue
        #
        #     dji_txt_docs.append(dj_doc)

        # logger.info(f'{len(dji_txt_docs)=}, {dji_txt_docs[:10]}')

        # old_txt_messages = [
        #     m for m in all_messages if m.document in dji_txt_docs
        # ]

        # docs_names = []

        # txt_messages = []
        # sorted(old_txt_messages, key=lambda txt_msg: txt_msg.id)
        # txt_messages = old_txt_messages

        # for txt_msg in reversed(old_txt_messages):
        #
        #     if txt_msg.document.file_name in docs_names:
        #         logger.info(f'maybe this doc?')
        #         continue
        #
        #     if txt_msg.document not in dji_txt_docs:
        #         # logger.info(f'skip no docs')
        #         continue
        #
        #     txt_messages.append(txt_msg)
        #     docs_names.append(txt_msg.document.file_name)

        # with open('.ids', 'w') as w:
        #     w.writelines([f'{m.id}\n' for m in txt_messages])

        # logger.info(f'{len(txt_messages)=}')

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

        pieces_to_delete = []

        async def gen_txt_files_from_orm():

            # for each file in doc
            # make data
            hashes = []
            files = []
            dict_files = {}
            # for doc in docs:
            for dj_piece in dj_pieces:

                doc = dj_piece.message.document

                file_name = doc.file_name
                if not file_name:
                    logger.info(f'not name: {dj_piece=}, {doc=}')
                    quit()

                txt_name = file_name.replace('.data', '.txt')
                # logger.info(f'{txt_name=}')

                if not dict_files.get(txt_name):
                    dict_files[txt_name] = ''

                if dj_piece.begin is None:
                    logger.info(f'no: {dj_piece=}, {doc=}')
                    pieces_to_delete.append(dj_piece)

                dict_files[txt_name] += f'{dj_piece.begin}|' \
                                        f'{dj_piece.length}|' \
                                        f'{dj_piece.info_hash}\n'

            for n, d in dict_files.items():
                files.append([n, d.encode('utf8')])

            return files

        dj_all_txt_bytes = [
            [
                name, data
            ] for name, data in await gen_txt_files_from_orm()
        ]

        logger.info(f'{len(dj_all_txt_bytes)=}')

        if pieces_to_delete:
            logger.info(f'{pieces_to_delete=}')
            logger.info(f'{len(pieces_to_delete)=}')
            logger.info(f'redown')
            for piece in pieces_to_delete:
                piece: DjangoTorrentPiece
                piece.delete()

            return

        # logger.info(f'{dj_all_txt_bytes=}')
        # quit()

        # all_txt_bytes = [
        #     [
        #         name, data
        #     ] for name, data in await get_txt_files(
        #         [f.document for f in txt_messages], None
        #     )
        # ]
        #
        # logger.info(f'{len(all_txt_bytes)=}')

        # ll = 0
        # for t in all_txt_bytes:
        #     kt, dt = t
        #     for d in dj_all_txt_bytes:
        #         kd, dd = d
        #         if kt == kd:
        #             logger.info(f'{kt}, {dt=}')
        #             logger.info(f'{kd}, {dd=}')
        #             #
        #             # and dt == dd:
        #             # logger.info(f'ok!')
        #             # ll += 1
        #             # break
        #
        # logger.info(f'check_{ll=}')

        # version = 6
        all_txt_bytes = dj_all_txt_bytes
        ln = len(all_txt_bytes)
        # quit()
        new_tree = True
        t = 0
        while all_txt_bytes:

            t += 1

            split = 11
            some_txt_bytes = []

            logger.info(f'{t}/{int(ln/split)}')
            for _ in range(0, split):
                try:
                    pop = all_txt_bytes.pop()
                    # name, data = pop
                    # logger.info(f'{pop=}')
                    # if b'7b9c6609f2bee84a2d7618191e797c252aae8baf' in data:
                    #     some_txt_bytes.append(pop)
                    #
                    # if b'59286e3d01243e6d01fa82d37e36be4030bf0354' in data:
                    #     some_txt_bytes.append(pop)
                    #
                    some_txt_bytes.append(pop)
                except IndexError:
                    pass

            if not some_txt_bytes:
                continue

            # logger.info(f'{some_txt_bytes=}')

            # while t < 24:
            #     t += 1
            #     logger.info(f'skip {t=}')
            #
            # if t > 29:
            #     break

            while True:
                try:
                    await self._merge_some_version5(
                        txt_bytes=some_txt_bytes,
                        dj_pieces=dj_pieces,
                        out_dir=out_dir,
                        rebuild_tree=new_tree
                    )
                    break
                except Exception as exc:
                    log_stack.error('exc')
                    logger.info(f'{exc=}'[:512])
                    await asyncio.sleep(60)
                    continue

            new_tree = False

            # for info, some in some_txt_bytes:
            #     Path(f'.data_tmp/{info}').touch()

            # all_txt_bytes = all_txt_bytes[10:]

        # txt_bytes = [[file_name1, bytes_from_this_file], ...]
        # file_bytes = {file_name1: data_file_bytes], ...}

        logger.info(f'end merging: {self.info_hash}')
        return True

    async def _merge_some_version5(
            self,
            txt_bytes,
            dj_pieces,
            out_dir,
            rebuild_tree=False
    ):

        client = None

        file_bytes = {}
        for txt in txt_bytes:
            txt_file, txt_bt = txt

            l = len(re.findall('_', txt_file))
            if l == 1:
                info_hash = txt_file.split('_')[1].split('.')[0]
            if l == 2:
                info_hash = txt_file.split('_')[2].split('.')[0]

            # logger.info(f'{txt_file=}')
            dj_piece = [
                x for x in dj_pieces if (
                        info_hash in x.info_hash
                )][0]

            tmp_path = f'.data_tmp/{info_hash}'
            # if os.path.isfile(f'.data_tmp/{info_hash}'):
            #     continue

            document = dj_piece.message.document

            # if os.path.isfile(tmp_path) and os.stat(tmp_path).st_size != 0:
            #     with open(tmp_path, 'rb') as f:
            #         file_data = BytesIO(f.read())
            #
            #     file_bytes[txt_file] = file_data
            #     continue

            size = document.file_size
            if size <= 20971520:
                # logger.info(f'download')
                while True:
                    try:
                        file_bytes[txt_file] = await self.bot.download(
                            document.file_id
                        )
                        break
                    except Exception as exc:
                        logger.info(f'{exc=}'[:512])
                        await asyncio.sleep(20)

                # with open(tmp_path, 'wb') as f:
                #     f.write(file_bytes[txt_file].read())
                #
                # file_bytes[txt_file].seek(0)
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
                        logger.info(f'{exc=}'[:512])
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
                            logger.info(f'{exc=}'[:512])
                            await asyncio.sleep(20)

                    # with open(tmp_path, 'wb') as f:
                    #     f.write(file_data.read())

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
            version=6,
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
