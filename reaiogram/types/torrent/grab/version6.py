import gc
import os
import re
import asyncio
import random
import time
import psutil
import tracemalloc
import inspect
import logging
import pyrogram

from typing import Union
from operator import itemgetter
from typing import BinaryIO
from pathlib import Path
from io import BytesIO
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types import BufferedInputFile, InputFile
from FastTelethonhelper.FastTelethon import (
    ParallelTransferrer, TypeLocation,
)

from telethon import utils

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

from pyrogram.file_id import FileId as PyrogramFileId
from tg_file_id.file_id import FileId
from tg_file_id.file_unique_id import FileUniqueId

TG_CHAT_ID = secrets.bt.download.chat_id
TG_API_ID = secrets.bt.download.api_id
TG_API_HASH = secrets.bt.download.api_hash

# logging.basicConfig(level=logging.DEBUG)
# For instance, show only warnings and above
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logging.getLogger('pyrogram').setLevel(level=logging.WARNING)


async def yield_pyrogram_chunks(
        client: pyrogram.Client,
        file_id_obj,
        file_size
):
    async for chunk in client.get_file(file_id_obj, file_size, 0, 0):
        yield chunk


async def download_file_pyrogram(
        client: pyrogram.Client,
        message,
        out: BytesIO,
):
    # chunks = {}
    # num = -1

    # client.stream_media()
    logger.info(f'yield start')
    media = message.document

    file_id = PyrogramFileId.decode(media.file_id)
    file_size = getattr(media, "file_size", 0)
    async for chunk in client.get_file(file_id, file_size, 0, 0):
        out.write(chunk)

    return out
    logger.info(f'yield end')

    sem = asyncio.Semaphore(5)

    async def read_chunk(_num, _chunk):
        async with sem:
            logger.info(f'{chunk=}, {len(_chunk)=}')
        return _num, _chunk

    tasks = []
    for n, chunk in chunks.items():
        task = asyncio.create_task(read_chunk(n, chunk))
        tasks.append(task)

    logger.info(f'gather start')
    await asyncio.gather(*tasks)
    logger.info(f'gather end')

    logger.info(f'write start')
    for n in range(0, len(chunks.keys())):
        out.write(chunks[num])

    logger.info(f'write end')
    return out


async def download_file_telethon(
    client: TelegramClient,
    location: TypeLocation,
    out: BinaryIO,
    progress_callback: callable = None,
) -> BinaryIO:
    size = location.size
    dc_id, location = utils.get_input_location(location)
    # We lock the transfers because telegram has connection count limits
    downloader = ParallelTransferrer(client, dc_id)
    downloaded = downloader.download(location, size)
    async for x in downloaded:
        out.write(x)
        if progress_callback:
            r = progress_callback(out.tell(), size)
            if inspect.isawaitable(r):
                try:
                    await r
                except BaseException:
                    pass

    return out


async def new_client(
        tp,
        client: Union[TelegramClient, pyrogram.Client],
):

    logger.info(f'{tp=}, {client=}')
    if tp == 'telethon':
        client: TelegramClient
        if client:
            try:
                await client.disconnect()
            except:
                pass

            # try:
            #     await client.close()
            # except:
            #     pass

        client = TelegramClient(
            '.tg_download_session', TG_API_ID, TG_API_HASH,
            auto_reconnect=False,
            proxy=('socks5', secrets.temp.proxy.adr, secrets.temp.proxy.port),
        )
        await client.connect()
        # await client.start()

    elif tp == 'pyrogram':
        client: pyrogram.Client
        if client:
            logger.info(f'disconnect, {client=}')
            await client.disconnect()

        client = pyrogram.Client(
            f'.tg_download_pyrogram',
            api_id=secrets.bt.download.api_id,
            api_hash=secrets.bt.download.api_hash,
            workers=8,
            max_concurrent_transmissions=8,
            proxy={
                "scheme": "socks5",
                "hostname": secrets.temp.proxy.adr,
                "port": secrets.temp.proxy.port,
            }

        )

        await client.connect()
        # await client.get_me()

    return client


# client = asyncio.run(new_client('pyrogram', None, True))
# client.run()
# asyncio.run(new_client('telethon', None))


class TorrentGrabVersion6(
    DefaultTorrent,
    AbstractMergedTelegram
):

    async def check_complete_for_grab5(self):

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

    async def grab_torrent_from_telegram_version6(
            self,
            out_dir,
            version=6
    ):

        # create_dir(out_dir)
        # messages = DjangoTgMessage.objects.filter(caption=)
        # dj_documents = DjangoTgDocument.objects.all()
        # documents = [
        #     x for x in dj_documents if (
        #             'txt' in x.file_name
        #     ) and self.info_hash in x.file_name
        # ]
        #
        # logger.info(f'{len(documents)}')

        # all_messages = DjangoTgMessage.objects.filter().all()
        #
        # logger.info(f'g.{len(all_messages)=}')
        # cache variant
        # with open('.txt_ids', 'r') as ir:
        #     ids = [int(x.splitlines()[0]) for x in ir.readlines()]
        #
        # txt_messages = [
        #     m for m in all_messages if m.id in ids
        # ]
        # life variant

        # all docs in db
        # dj_documents = DjangoTgDocument.objects.all()
        # logger.info(f'g.{len(dj_documents)=}')

        # all pieces in db by torrent
        dj_pieces = DjangoTorrentPiece.objects.filter(
            torrent=await self.from_orm(),
            # version=6,
        )
        logger.info(f'g.{len(dj_pieces)=}')

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

                if dj_piece.info_hash in exist_pieces_hashes:
                    logger.info(f'{dj_piece.info_hash} exist in tree')
                    continue

                dict_files[txt_name] += f'{dj_piece.begin}|' \
                                        f'{dj_piece.length}|' \
                                        f'{dj_piece.info_hash}\n'

            for n, d in dict_files.items():
                if not d:
                    logger.info(f'skip file:{n=}')
                    continue

                files.append([n, d.encode('utf8')])

            return sorted(files, key=itemgetter(0))

        new_tree = True
        for check_func in (
                os.path.isfile,
                os.path.islink,
                os.path.isdir,
        ):
            try:
                if check_func(f'{out_dir}/{self.name}'):
                    new_tree = False
                    logger.info(f'new_tree = False')
            except Exception as exc:
                log_stack.error('ch')

        exist_pieces_hashes = []
        if not new_tree:
            logger.info(f'start check available.1')
            available_pieces = self.yield_available_pieces(out_dir)
            logger.info(f'start check available.2')
            exist_pieces_hashes = [from_bytes_to_hex(p.hash) for p in available_pieces]
            logger.info(f'checked available')
            # logger.info(f'{available_pieces=}')
            # logger.info(f'{exist_pieces_hashes=}')

        # dj_all_txt_bytes = [
        #     [
        #         name, data
        #     ] for name, data in await gen_txt_files_from_orm()
        # ]

        dj_all_txt_bytes = await gen_txt_files_from_orm()

        logger.info(f'g.{len(dj_all_txt_bytes)=}')

        if pieces_to_delete:
            logger.info(f'{pieces_to_delete=}')
            logger.info(f'{len(pieces_to_delete)=}')
            logger.info(f'redown: {self.info_hash=}')
            # for piece in pieces_to_delete:
            #     piece: DjangoTorrentPiece
            #     piece.delete()

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

        logger.info(f'g.f:{new_tree=}')
        t = 0
        split_files = 5
        while all_txt_bytes:

            t += 1

            some_txt_bytes = []

            split = 0
            while True:

                split += 1
                pop = all_txt_bytes.pop()
                some_txt_bytes.append(pop)

                name, data = pop

                try:
                    new_pop = all_txt_bytes[-1]
                except IndexError:
                    split = split_files
                    break

                new_name, new_data = new_pop

                if name != new_name and split >= split_files:
                    break

            logger.info(f'{t}/{int(ln/split)+1}')

            if not some_txt_bytes:
                continue

            while True:
                try:
                    await self._merge_some_version6(
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

    async def _merge_some_version6(
            self,
            txt_bytes,
            dj_pieces,
            out_dir,
            rebuild_tree=False
    ):

        # tg_client = None
        tg_client = await new_client('pyrogram', None)

        async def download_task(
                size,
                file_bytes,
                txt_file,
                document,
                client,
                limiter,
                i_hash,
        ):

            if file_bytes.get(txt_file):
                return

            # if False:
            if size <= 20971520:
                # logger.info(f'download')
                while True:
                    try:
                        async with limiter['bot']:
                            file_bytes[txt_file] = await self.bot.download(
                                document.file_id
                            )
                            break
                    except (
                        TelegramRetryAfter, TelegramBadRequest
                    ) as exc:
                        tm = self.bot.get_retry_timeout(exc)

                        self.dp.wait_upload = tm
                        logger.info(f'sleep {tm=}')
                        await asyncio.sleep(tm+random.randint(2, 10))
                        self.dp.wait_upload = 0
                    except Exception as exc:
                        logger.info(f'{exc=}'[:512])
                        await asyncio.sleep(20)

                # with open(tmp_path, 'wb') as f:
                #     f.write(file_bytes[txt_file].read())
                #
                # file_bytes[txt_file].seek(0)

            else:
                # logger.info(f'rewrite')
                # return

                async def sleep_send(file_id):
                    # await asyncio.sleep(2)
                    while True:
                        try:
                            await self.bot.send_document(
                                TG_CHAT_ID, file_id,
                                caption=i_hash
                            )
                            break
                        except (
                            TelegramRetryAfter, TelegramBadRequest
                        ) as exc:
                            logger.info(f'grab.wait.bot {tm=}')
                            tm = self.bot.get_retry_timeout(exc)
                            await asyncio.sleep(tm+random.randint(2, 10))

                async with limiter['client']:

                    tp = 'pyrogram'
                    if not client:
                        client = await new_client(tp, None)

                    # asyncio.create_task(
                    await sleep_send(document.file_id)
                    # )
                    await asyncio.sleep(2)

                    del_ids = []
                    file_data = None

                    messages = None
                    while not messages:
                        try:
                            if tp == 'telethon':
                                messages = await client.get_messages((await self.bot.me()).id)
                            elif tp == 'pyrogram':
                                client: pyrogram.Client
                                messages = []
                                async for message in client.get_chat_history(
                                    chat_id=(await self.bot.me()).username,
                                    limit=20
                                ):
                                    if not message:
                                        continue

                                    if message.document:
                                        if i_hash in message.document.file_name:
                                            messages.append(message)
                                            continue

                                    if message.caption:
                                        if i_hash in message.caption:
                                            messages.append(message)
                                            continue

                                    if message.text:
                                        if i_hash in message.text:
                                            messages.append(message)
                                            continue

                            break
                        except Exception as exc:
                            logger.info(f'{exc=}'[:512])
                            await asyncio.sleep(5+random.randint(5, 10))
                            client = await new_client(tp, client)
                            continue

                    while True:

                        try:
                            msg = messages.pop()
                            # await asyncio.sleep(0)
                        except IndexError:
                            break
                            # try:
                            #     messages = await client.get_messages((await self.bot.me()).id)
                            #     logger.info(f're.msg, {self.info_hash=}')
                            # except Exception as exc:
                            #     logger.info(f'{exc=}')
                            #     client = await new_client(client)

                            # await asyncio.sleep(30)
                            # continue

                        # logger.info(f'{msg=}\n{dir(msg)=}')
                        # await asyncio.sleep(2)
                        # if not hasattr(msg, 'caption'):
                        #     del_ids.append(msg.id)
                        #     await asyncio.sleep(1)
                        #     continue
                        if not msg:
                            return

                        # del_ids.append(msg.id)
                        # if tp == 'telethon':
                        #     if not msg.message:
                        #         continue
                        #     text = msg.message
                        # elif tp == 'pyrogram':
                        #     if not msg.caption:
                        #         continue
                        #     text = msg.caption

                        # if info_hash not in text:
                        #     del_ids.append(msg.id)
                        #     continue

                        # file_data = ()
                        while True:
                            try:
                                file_data = BytesIO()
                                #BinaryIO()
                                if tp == 'telethon':
                                    blob = await download_file_telethon(
                                        client, msg.document,
                                        file_data,
                                    )
                                    file_data = blob

                                # blob = await client.download_media(
                                #     msg, file=bytes
                                # )
                                # file_data = BytesIO(blob)
                                # file_data.read()
                                # file_data.seek(0)

                                # logger.info(f'{len(file_data)=}')
                                # logger.info(f'{len(blob)=}')
                                elif tp == 'pyrogram':
                                    blob = await download_file_pyrogram(
                                        client, msg, file_data
                                    )
                                    # blob = await client.download_media(
                                    #     message=msg,
                                    #     in_memory=True
                                    # )
                                    file_data = blob

                                break
                            except Exception as exc:

                                client = await new_client(tp, client)
                                logger.info(f'{exc=}'[:512])
                                await asyncio.sleep(20)
                                continue

                        # with open(tmp_path, 'wb') as f:
                        #     f.write(file_data.read())

                        file_data.seek(0)
                        break

                    if file_data is None:
                        logger.info(f'null.data, {file_data=}')
                        return

                    try:
                        if tp == 'telethon':
                            await client.delete_messages(TG_CHAT_ID, del_ids)
                        elif tp == 'pyrogram':
                            await client.delete_messages(TG_CHAT_ID, del_ids)
                    except Exception as exc:
                        logger.info(f'{exc=}')
                        # client = new_client(client)
                        # logger.info(f'{exc}')
                        await asyncio.sleep(20)

                    file_bytes[txt_file] = file_data

        limiter = {
            'client': asyncio.Semaphore(2),
            'bot': asyncio.Semaphore(4),
        }

        file_bytes = {}
        tasks = []

        for txt in txt_bytes:
            txt_file, txt_bt = txt

            if file_bytes.get(txt_file):
                logger.info(f'file.skip: {txt_file=}')
                continue

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

            task = asyncio.ensure_future(
                download_task(
                    size, file_bytes, txt_file, document, tg_client, limiter,
                    dj_piece.info_hash
                )
            )
            tasks.append(task)

        logger.info(f'{len(file_bytes.keys())=}, {self.info_hash=}')
        await asyncio.gather(*tasks)
        logger.info(f'{len(file_bytes.keys())=}, {self.info_hash=}')

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

        if tg_client:
            try:
                await tg_client.disconnect()
            except Exception as exc:
                logger.info(f'{exc=}')

        # merge_some end
