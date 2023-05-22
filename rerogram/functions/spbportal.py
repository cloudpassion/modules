import pyrogram
import asyncio
import re
import ujson as json

from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup
from pyrogram import Client as PyrogramClient
from pyrogram.types import Message as PyrogramMessage
from pyrogram.types import InputMediaPhoto, InputMediaDocument
from pyrogram.errors.exceptions.flood_420 import FloodWait

from ..client import MyAbstractTelegramClient
from ..db.types.message import MyEventMessageDatabase

from ..django_telegram.django_telegram.datamanager.models import (
    Message as DjangoTelegramMessage,
    SpbPortalPagePost as DjangoSpbPortalPagePost,
    SpbPortalProblem as DjangoSpbProblem
)

from ..rewrite import MyPyrogramRewrite
from jkh.spb_portal import (
    SpbPortal, SpbPortalProblem,
    SpbPortalProblemPagePost
)

from config import settings
from log import logger, log_stack


class MyPyrogramSpbPortal(
    MyAbstractTelegramClient,
    MyPyrogramRewrite,
    # PyrogramClient,
):

    async def spb_new_or_update_post(
            self,
            problem: SpbPortalProblem, channel_id, chat_id
    ):
        async def update_problem_db(
                _problem: SpbPortalProblem,
                _message: DjangoTelegramMessage,
        ):
            _problem_db = self.db.add_data(
                'SpbPortalProblem',
                problem.id,
                **{
                    'message': _message,

                    'text': _message.text,
                    'link': _problem.link,
                    'type': _problem.type,

                    'status': _problem.status,
                    'title': _problem.title,
                    'date': _problem.date,

                    'category': _problem.category,
                    'reason': _problem.reason,
                    'solved_under': int(
                        _problem.solved_under.strftime('%s')
                    ) if _problem.solved_under else None,

                    'author_name': _problem.author_name,
                    'author_id': _problem.author_id,

                    'join': _problem.join,
                },
            )
            return _problem_db

        async def update_problem_post(
                _post_num: int,
                _post: SpbPortalProblemPagePost,
                _db_problem: DjangoSpbProblem,
                _message: DjangoTelegramMessage,
                _message_ids: list,
                _post_files: list,
        ):
            _db_post = self.db.add_data(
                'SpbPortalPagePost',
                _db_problem.id,
                **{
                    'id': _db_problem.id,
                    'message': _message,
                    'post_num': _post_num,

                    'title': _post.title,
                    'author': _post.author,
                    'date': _post.date,
                    'text': _post.text,
                    'status': _post.status,

                    'chat_message_ids': _message_ids,
                    'post_files': _post_files,
                }
            )
            return _db_post

        if problem.type != 'hidden':

            await problem.parse_page()

            while not problem.container_found:
                logger.info(f'research container: {problem.id}')
                await problem.get_page()
                await problem.parse_page()

                if not problem.container_found:
                    await asyncio.sleep(10)

        problem_db: DjangoSpbProblem = self.db.select(
            'SpbPortalProblem',
            select_id=problem.id,
        )

        underlines, bolds, italic, links = [], [], [], []
        if problem.author_name:
            italic.append(problem.author_name)

        post_text = f'{problem.title}\n'

        if problem.category:
            underlines.append(problem.category)
            post_text += f'{problem.category}\n'

        if problem.author_name:
            user_link = (
                f'Заявки',
                f'{problem.host_url}/accounts/{problem.author_id}/'
            )
            post_text += f'{problem.author_name} <- {user_link[0]}\n'
            links.append(user_link)

        if problem.date:
            problem_date = problem.date.strftime('%d.%m.%Y')
        else:
            problem_date = ''

        post_text += f'\n[{problem.lang_ru[problem.type]} проблема] ' \
                     f'{problem_date}\n'

        if problem.type == 'open':
            post_text += f'{problem.link}\n'
        elif problem.type == 'hidden':
            post_text += 'Информация о проблеме доступна только в личном кабинете\n'
            italic.append('Информация о проблеме доступна только в личном кабинете')

        post_text += f'[{problem.lang_ru[problem.status]}] '

        if problem.type == 'open':
            post_text += f'Присоединились: {"⃣".join((*(str(problem.join)), " "))}'
            if problem.solved_under:
                solved_date = problem.solved_under.strftime(
                    '%d.%m.%Y') if problem.solved_under else None
                if solved_date:
                    post_text += f'\nРешение до {solved_date}'
                    bolds.append(solved_date)

        elif problem.type == 'hidden':
            logger.info(f'{problem.link}')
            page_link = (
                f'странице {problem.link.split("=")[2]}',
                problem.link
            )
            post_text += f'\nНайдена на {page_link[0]}.'
            links.append(page_link)

        logger.info(f'1')
        entities, added_offset, entities_edited = await self.add_entites(
            post_text, underlines=underlines, italic=italic, links=links,
            bolds=bolds,
        )
        logger.info(f'{entities=}')
        #
        # logger.info(f'{post_text=}')
        # logger.info(f'{problem_db}')
        if problem_db:
            logger.info(f'11')
            check_problem_msg = await self.get_messages(
                problem_db.message.chat.id, message_ids=[problem_db.message.id, ]
            )
            logger.info(f'111')
            if check_problem_msg and check_problem_msg[0].empty:
                logger.info(f'delete: {problem_db=}')
                DjangoSpbProblem.objects.filter(id=problem.id).delete()
                problem_db = None

        logger.info(f'a2')
        post_photos = []
        if not problem_db:
            if not problem.type == 'hidden':
                logger.info(f'{problem.items[0].files}')
                post_photos = [
                    x for x in problem.items[
                        0
                    ].files if re.search(
                        '[\.jpg|\.png|\.bmp]$',
                        f'{x.file_name.lower()}'
                    )
                ]

            if post_photos:
                if len(post_photos) > 1:
                    while True:
                        try:
                            _channel_post = await self.send_media_group(
                                channel_id,
                                media=[InputMediaPhoto(
                                    media=post_photos[0].path,
                                    caption=post_text, caption_entities=entities,
                                ), *(InputMediaPhoto(
                                    media=x.path,
                                ) for x in post_photos[1:9]
                                )],
                            )
                            break
                        except FloodWait as exc:
                            await self.parse_flood('FL1', exc)
                        except Exception as exc:
                            log_stack.error(f'FL1')
                            await asyncio.sleep(120)
                else:
                    while True:
                        try:
                            _channel_post = await self.send_photo(
                                channel_id, photo=post_photos[0].path,
                                caption=post_text, caption_entities=entities,
                            )
                            break
                        except FloodWait as exc:
                            await self.parse_flood('FL2', exc)
                        except Exception as exc:
                            log_stack.error(f'FL2')
                            await asyncio.sleep(120)
            else:
                while True:
                    try:
                        _channel_post = await self.send_message(
                            channel_id, text=post_text,
                            entities=entities, disable_web_page_preview=True,
                            disable_notification=True,
                        )
                        break
                    except FloodWait as exc:
                        await self.parse_flood('FL3', exc)
                    except Exception as exc:
                        log_stack.error(f'FL3')
                        await asyncio.sleep(120)

            if isinstance(_channel_post, list):
                _channel_post = _channel_post[0]

            db_temp = await self.database_message(
                message=_channel_post,
            )

            while True:

                db_temp = self.db.select(
                    'message', _channel_post.chat.id,
                    id=_channel_post.id
                )

                if db_temp:
                    break

                logger.info(f'sl1spb')
                await asyncio.sleep(0.1)

            db_channel_msg = db_temp
            db_chat_msg = db_temp.discuss_message
            logger.info(f'{db_channel_msg=}')
            logger.info(f'{db_chat_msg=}')

            problem_db = await update_problem_db(
                problem, db_channel_msg,
            )

        if not problem_db:
            logger.info(f'no pdb')
            return

        channel_post: DjangoTelegramMessage = problem_db.message
        chat_message: DjangoTelegramMessage = problem_db.message.discuss_message

        post_text += f'\n\nОбсудить: https://t.me/' \
                     f'{problem.settings.spb.tg.username}/' \
                     f'{problem_db.message.id}?comment=' \
                     f'{problem_db.message.discuss_message.id}'

        logger.info(f'a3')
        if post_text != f'{problem_db.text}':
            try:
                if channel_post.media_ids:
                    try:
                        await self.edit_message_caption(
                            channel_id, message_id=channel_post.id,
                            caption=post_text, caption_entities=entities,
                        )
                    except:
                        log_stack.error(f'CH1')
                else:
                    try:
                        await self.edit_message_text(
                            channel_id, message_id=channel_post.id,
                            text=post_text, entities=entities,
                            disable_web_page_preview=True,
                        )
                    except:
                        log_stack.error(f'CH2')
            except:
                pass

            channel_post.text = post_text
            problem_db = await update_problem_db(
                problem, channel_post,
            )

        while not channel_post.discuss_message:
            channel_post = self.db.select(
                'message',
                channel_id,
                id=channel_post.id,
            )
            if not channel_post.discuss_message:
                await asyncio.sleep(0.1)
                logger.info(f'sl6')

        logger.info(f'a4')
        for post_num, post in enumerate(problem.items):
            logger.info(f'{post_num=}, {post=}')
            post: SpbPortalProblemPagePost

            chat_messages = []

            underlines, italic, links = [], [], []

            post_date = post.date.strftime('%d.%m.%Y %H:%M')
            # logger.info(f'{post.text=}')
            if post.text:
                soup = BeautifulSoup(f'{post.text}', features='html.parser')
                # kill all script and style elements
                for script in soup(["script", "style", 'i', 'a']):
                    script.extract()    # rip it out

                _text = soup.get_text()
            else:
                _text = ''

            logger.info(f'a5')

            _text = _text.replace(
                'Часть текста скрыта модератором портала, '
                'так как содержит личную информацию пользователя.', ''
            )
            post_text = f'{problem.link}\n\n' \
                        f'{post_date}\n' \

            if post.author:
                post_text += f'{post.author} {post.title}\n'
            else:
                post_text += f'{post.title}\n'

            if post.status:
                post_text += f'{post.status}\n'

            if post.text:
                post_text += f'\n{_text}'

            post_caption = post_text
            if len(post_caption) >= 1024:
                post_caption = "".join(
                    post_caption[0:1024]
                )

            italic.append(post.author)

            entities, added_offset, entities_edited = await self.add_entites(
                post_text, underlines=underlines, italic=italic, links=links,
            )
            logger.info(f'{post_num=}, {post=}')
            # logger.info(f'{post_text=}')

            db_post: DjangoSpbPortalPagePost = self.db.select(
                'SpbPortalPagePost',
                problem.id,
                post_num=post_num,
            )

            if db_post:
                _chat_message = await self.get_messages(
                    db_post.message.chat.id, message_ids=[db_post.message.id, ]
                )
                if _chat_message and _chat_message[0].empty:
                    await self.delete_messages(
                        chat_id, message_ids=json.loads(db_post.chat_message_ids)
                    )
                    logger.info(f'delete: {db_post=}')
                    all_posts = DjangoSpbPortalPagePost.objects.filter(
                        id=problem.id,
                    ).all()
                    for ps in all_posts:
                        ps.delete()

                    db_post = None

            #
            logger.info(f'{post.files=}')
            if not db_post:
                logger.info(f'{post.files=}')
                post_photos = [
                    x for x in post.files if re.search(
                        '[\.jpg|\.png|\.bmp]$',
                        f'{x.file_name.lower()}'
                    )
                ]
                logger.info(f'{post_photos=}')
                post_files = [
                    x for x in post.files if x not in post_photos
                ]
                # if not chat_message:
                #     reply_to = chat_msg.id
                # else:
                reply_to = chat_message.id

                if post_num == 0:
                    post_photos = []

                if post_photos:
                    if len(post_photos) > 1:
                        chat_messages.extend(
                            await self.send_media_group(
                                chat_id,
                                media=[InputMediaPhoto(
                                    media=post_photos[0].path,
                                    caption=post_caption, caption_entities=entities,
                                ), *(InputMediaPhoto(
                                    media=x.path,
                                ) for x in post_photos[1:9]
                                )],
                                reply_to_message_id=reply_to,
                            )
                        )

                        reply_to = chat_messages[0].id
                    else:
                        chat_messages.append(
                            await self.send_photo(
                                chat_id, photo=post_photos[0].path,
                                caption=post_caption,
                                caption_entities=entities,
                                reply_to_message_id=reply_to,
                            )
                        )
                        reply_to = chat_messages[0].id

                else:
                    chat_messages.append(
                        await self.send_message(
                            chat_id, text=post_text, entities=entities,
                            reply_to_message_id=reply_to,
                            disable_web_page_preview=True,
                        )
                    )
                    reply_to = chat_messages[0].id

                # if not isinstance(chat_message, list):
                #     chat_message = [chat_message, ]

                if post_files:

                    # if not post_photos:
                    #     file_caption = '_'post_caption
                    #     file_entities = entities
                    # else:
                    file_caption = '_'
                    file_entities = None

                    if len(post_files) > 1:
                        chat_messages.extend(
                            await self.send_media_group(
                                chat_id,
                                media=[InputMediaDocument(
                                    media=post_files[0].path,
                                    caption=file_caption,
                                    caption_entities=file_entities,
                                ),
                                    *(
                                        InputMediaDocument(
                                            media=x.path,
                                            caption='_',
                                        ) for x in post_files[1:10]
                                    ),
                                ],
                                reply_to_message_id=reply_to,
                            )
                        )
                    else:
                        chat_messages.append(
                            await self.send_document(
                                chat_id, document=post_files[0].path,
                                file_name=post_files[0].file_name,
                                force_document=True,
                                caption=file_caption,
                                caption_entities=file_entities,
                                reply_to_message_id=reply_to,
                            )
                        )

                for ch_ms in chat_messages:
                    _temp_caption = post_caption
                    if ch_ms.caption:
                        if not ch_ms.caption or ch_ms.caption == '_':
                            _temp_caption = f'\n\nОбсудить: https://t.me/' \
                                           f'{problem.settings.spb.tg.username}/' \
                                           f'{problem_db.message.id}' \
                                           f'?comment=' \
                                           f'{ch_ms.id}'
                        else:
                            temp = f'\n\nОбсудить: https://t.me/' \
                                           f'{problem.settings.spb.tg.username}/' \
                                           f'{problem_db.message.id}' \
                                           f'?comment=' \
                                           f'{ch_ms.id}'

                            if len(_temp_caption) + len(temp) < 1024:
                                _temp_caption += temp

                            else:
                                _temp_caption = "".join(
                                    _temp_caption[0:(1024-len(temp)-1)]
                                ) + temp

                    if ch_ms.caption:
                        if _temp_caption != ch_ms.caption:
                            try:
                                await self.edit_message_caption(
                                    ch_ms.chat.id, message_id=ch_ms.id,
                                    caption=_temp_caption,
                                )
                            except:
                                log_stack.error(f'spb_cpt')

                event = chat_messages[0]
                db_chat_msg = await self.database_message(
                    message=event
                )
                # logger.info(f'{chat_message=}')
                while not db_chat_msg:
                    db_chat_msg = self.db.select(
                        'message',
                        chat_id,
                        id=chat_messages[0].id,
                    )
                    logger.info(f'{db_chat_msg=}')
                    if not db_chat_msg:
                        await asyncio.sleep(0.1)

                post.text = post_text
                db_post = await update_problem_post(
                    post_num, post, problem_db, db_chat_msg,
                    _message_ids=[x.id for x in chat_messages],
                    _post_files=[x.path for x in post.files]
                )

            if not db_post:
                logger.info(f'no db')
                quit()

            chat_message: DjangoTelegramMessage = db_post.message

            temp = f'\n\nОбсудить: https://t.me/' \
                   f'{problem.settings.spb.tg.username}/' \
                   f'{problem_db.message.id}?comment=' \
                   f'{chat_message.id}'

            if len(post_text) + len(temp) < 4096:
                post_text += temp

            else:
                post_text = "".join(
                    post_text[0:(4096-len(temp)-1)]
                ) + temp

            if post_text != f'{db_post.text}':
                try:
                    if chat_message.media_ids:
                        temp = f'\n\nОбсудить: https://t.me/' \
                               f'{problem.settings.spb.tg.username}/' \
                               f'{problem_db.message.id}' \
                               f'?comment=' \
                               f'{chat_message.id}'

                        if post_caption == '_':
                            post_caption = temp
                        elif len(post_caption) + len(temp) < 1024:
                            post_caption += temp
                        else:
                            post_caption = "".join(
                                post_caption[0:(1024-len(temp)-1)]
                            ) + temp

                        await self.edit_message_caption(
                            chat_id, message_id=chat_message.id,
                            caption=post_caption, caption_entities=entities,
                        )
                    else:
                        await self.edit_message_text(
                            chat_id, message_id=chat_message.id,
                            text=post_text, entities=entities,
                            disable_web_page_preview=True,
                        )
                except:
                    log_stack.error(f'check')

                post.text = post_text
                db_post = await update_problem_post(
                    post_num, post, problem_db, chat_message,
                    _message_ids=db_post.chat_message_ids,
                    _post_files=db_post.post_files
                )

        await asyncio.sleep(5)

    async def spb_init(self, channel_id, chat_id):

        spb = SpbPortal(
            mkd_id=settings.spb.mkd_id, settings=settings,
        )
        allpg = await spb.all_problems(max_page=1)
        spb.problems.sort(key=lambda x: x.date, reverse=True)
        skip_first = 0
        # break_on = 52
        # break_on = 26
        break_on = 1000
        count = 0
        # res = Counter([x.id for x in spb.problems])
        # logger.info(f'{res=}')

        test_problems = []
        for problem_num, problem in enumerate(reversed(spb.problems)):
            logger.info(f'{problem_num}: {problem.date}, {problem.title=}')

            # if problem.type == 'hidden':
            #     continue

            count += 1
            if count < skip_first:
                continue

            # test_problems.append(problem)
            await self.spb_new_or_update_post(problem, channel_id, chat_id)

            if count >= break_on:
                break

        if test_problems:
            for problem_num, problem in enumerate(reversed(test_problems)):
                logger.info(f'test:{problem_num}: {problem.date}, {problem.title=}')
                await self.spb_new_or_update_post(problem, channel_id, chat_id)
                break
        return


