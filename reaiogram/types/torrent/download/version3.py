import re
import asyncio
import random

from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import BufferedInputFile

from config import secrets, settings
from log import logger, log_stack

from reaiogram.types.torrent.default import DefaultTorrent, AbstractMergedTelegram

from ..default import (
    DjangoTorrentPiece,
)


class TorrentDownloadVersion3(
    DefaultTorrent,
    AbstractMergedTelegram
):

    # pieces pack at once. size don't exceed 20MB
    async def _download_some_pieces_version3(self):

        piece_size = self.pieces[0].length

        all_pieces_to_download = []
        while self.pieces:

            pieces_pack_to_download = []
            size = 0
            while size + piece_size < 20971520:

                try:
                    piece = self.pieces.pop()
                except IndexError:
                    break

                dj: DjangoTorrentPiece = await piece.from_orm()
                # while not dj:
                #     dj = await piece.from_orm()
                #     await asyncio.sleep(1)
                #     logger.info(f'{dj=}')

                if dj.message:
                    # logger.info(f'piece already downloaded')
                    continue

                if dj.resume_data:
                    logger.info(f'check downloading')
                    continue

                pieces_pack_to_download.append(piece)
                size += piece.length

            all_pieces_to_download.append(pieces_pack_to_download)

        asyncio.create_task(
            self._download_all_version3(all_pieces_to_download)
        )

    async def _download_all_version3(
            self, all_lists
    ):

        for piece_pack in all_lists:
            asyncio.create_task(
                self._mon_completed_and_upload_version3(piece_pack, all_lists)
            )

        # for piece in [item for sublist in all_lists for item in sublist]:
        #     await piece.download(to_bytes=True)

        pieces = [item.piece for sublist in all_lists for item in sublist]

        missing_pieces = set(self.metadata.pieces)
        for piece in self.metadata.pieces:
            if piece not in pieces:
                # logger.info(f'del {piece=} from downloading')
                # index = self.metadata.pieces.index(piece)
                missing_pieces.remove(piece)

        if not self.metadata.pieces:
            logger.info(f'no pieces to upload')
            return

        del pieces

        await self.download(
            # pieces,
            # self.metadata.pieces,
            missing_pieces,
            to_bytes=True,
        )

    async def _mon_completed_and_upload_version3(
            self, pieces_pack, all_lists
    ):
        for _piece in pieces_pack:
            try:
                index = self.metadata.pieces.index(_piece.piece)
                piece = self.metadata.pieces[index]
            except ValueError:
                continue

            while not piece.completed:
                await asyncio.sleep(10+random.randint(5, 15))

            # logger.info(f'complete:{piece=}')

        data = b''
        text = ''
        begin = 0
        for piece in pieces_pack.copy():
            # if not piece.piece.data:
            #     logger.info(f'no data in {piece=}')
            #     del pieces_pack[pieces_pack.index(piece)]
            #     continue

            piece.version = 3
            piece.begin = begin

            text += f'{begin}|{piece.info_hash}\n'
            data += piece.piece.data
            begin += len(piece.piece.data)

        caption = f'{self.info_hash}_{pieces_pack[0].info_hash}.txt'
        piece_file = BufferedInputFile(
            data,
            filename=f'{caption}.data'
        )
        txt_file = BufferedInputFile(
            text.encode('utf8'),
            filename=f'{caption}.txt'
        )

        async with self.upload_sem:
            for input_file in (txt_file, piece_file):
                while True:
                    try:
                        bt = secrets.bt.chat
                        if input_file is txt_file:
                            chat_id = bt.txt.id
                            thread_id = bt.txt.thread_id
                        else:
                            chat_id = bt.pieces.id
                            thread_id = bt.pieces.thread_id

                        message = await self.bot.send_document(
                            chat_id=chat_id,
                            message_thread_id=thread_id,
                            caption=self.info_hash,
                            document=input_file,
                        )

                        kwargs_data = await self.orm.message_to_orm(
                            message, prefix='sended'
                        )
                        break
                    except TelegramRetryAfter as exc:
                        try:
                            tm = int(re.findall('Retry in (.*?) seconds', exc)[0])
                        except Exception:
                            tm = 60
                        logger.info(f'sleep {tm=}')
                        await asyncio.sleep(tm+random.randint(1, 5))
                    except Exception as exc:
                        # log_stack.error('stack upload')
                        logger.info(f'sleep 20: {exc=}')
                        await asyncio.sleep(20)

        merged_message = kwargs_data['sended_merged_message']
        for piece in pieces_pack:

            piece.message = merged_message

            await piece._deep_to_orm()
            await piece.update_orm()

        # await asyncio.sleep(30)

        index = all_lists.index(pieces_pack)
        try:
            del all_lists[index]
        except Exception as exc:
            logger.info(f'{exc=}')

        while True:
            try:
                piece = pieces_pack.pop()
                index = self.metadata.pieces.index(piece)

                del piece
                del self.metadata.pieces[index]
            except IndexError:
                break
            except Exception as exc:
                logger.info(f'{exc=}')
                break

            # del piece.piece.data
        #
        logger.info(f'upload complete')
