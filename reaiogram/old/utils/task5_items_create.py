import ujson as json
# import coub_api
import aiohttp
import hashlib
import asyncio

from random import randint, uniform
from bs4 import BeautifulSoup
from aiogram.types import InputMediaPhoto

from config import settings, secrets
from log import logger, log_stack
# from reaiogram.db.schemas.lesson.task5.default import Task5DefaultDjangoORM


# async def create_default_items(dispatcher: Task5DefaultDjangoORM):
#
#     timeline_url = f'https://coub.com/api/v2/timeline/explore/' \
#                    f'random?order_by=&page={randint(10, 100)}'
#     while True:
#         try:
#             items_resp = coub_api.api.Timeline.request(
#                 'get', timeline_url
#             )
#             data = coub_api.schemas.timeline.TimeLineResponse(
#                 **json.loads(
#                     items_resp.content.decode('utf8')
#                 )
#             )
#             break
#         except Exception:
#             pass
#         logger.info(f'sleep')
#         await asyncio.sleep(1)
#
#     for coub in data.coubs:
#         logger.info(f'{coub.title=}')
#         coub: coub_api.schemas.coub.BigCoub
#
#         title = coub.title
#
#         permalink = coub.permalink
#         url = f'https://coub.com/view/{permalink}'
#
#         big_preview_url = coub.image_versions.template
#         thumb_preview_url = coub.first_frame_versions.template.replace('%{version}', 'small')
#
#         big_preview_name = big_preview_url.split('/')[-1].split('.')[0]
#         thumb_preview_name = thumb_preview_url.split('/')[-1].split('.')[0]
#
#         async with aiohttp.ClientSession() as session:
#             async with session.get(big_preview_url) as _resp:
#                 _content = await _resp.read()
#
#         #with open(f'cache/{big_preview_name}.jpg', 'wb') as wb:
#         #    wb.write(resp.content)
#         big_md5 = hashlib.md5(_content).hexdigest()
#         logger.info(f'{big_md5=}')
#
#         async with aiohttp.ClientSession() as session:
#             async with session.get(thumb_preview_url) as thumb_resp:
#                 thumb_content = await thumb_resp.read()
#
#         #    wb.write(resp.content)
#         thumb_md5 = hashlib.md5(thumb_content).hexdigest()
#         logger.info(f'{thumb_md5=}')
#
#         bg = await dispatcher.sql.search('files', 'md5', big_md5)
#         th = await dispatcher.sql.search('files', 'md5', thumb_md5)
#
#         logger.info(f'{bg=}')
#         logger.info(f'{th=}')
#
#         if th or bg:
#             continue
#
#         try:
#             send_photo_big = await dispatcher.bot.send_photo(
#                 secrets.aiogram.files_chat, photo=big_preview_url,
#                 caption=title, disable_notification=True
#             )
#
#             send_photo_thumb = await dispatcher.bot.send_photo(
#                 secrets.aiogram.files_chat, photo=thumb_preview_url,
#                 caption=title, disable_notification=True
#             )
#         except:
#             log_stack.info(f'error send photo')
#             continue
#
#         logger.info(f't: {dispatcher.sql.add_file}')
#         fl1 = await dispatcher.sql.add_file(
#             md5=big_md5, **{
#                 key: send_photo_big['photo'][-1][
#                     key] for key in ('file_id', 'file_unique_id', 'file_size')},
#             extension='jpg', tag='big_item_photo'
#         )
#
#         fl2 = await dispatcher.sql.add_file(
#             md5=thumb_md5, **{
#                 key: send_photo_thumb['photo'][0][
#                     key] for key in ('file_id', 'file_unique_id', 'file_size')},
#             extension='jpg', tag='thumb_item_photo'
#         )
#
#         logger.info(f'{fl1=}')
#         logger.info(f'{fl2=}')
#
#         headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; PPC Mac OS X 10_5_9 rv:2.0) '
#                                  'Gecko/20210602 Firefox/36.0'}
#         headers = {}
#
#         try:
#             async with aiohttp.ClientSession(
#                     headers=headers,
#                     ) as session:
#                 async with session.get(url=f'https://html.duckduckgo.com/html/?q={title}',
#                                        allow_redirects=True) as _resp:
#                     _content = await _resp.read()
#         except Exception:
#             continue
#
#         try:
#             soup = BeautifulSoup(_content, 'html.parser')
#             desc = soup.find('a', {'class': 'result__snippet'}).text
#             logger.info(f'{desc=}')
#         except:
#             continue
#
#         await dispatcher.sql.add_item(
#             thumb_file_id=fl2.file_id,
#             big_file_id=fl1.file_id,
#
#             item_price=uniform(1, 15),
#             count=randint(1, 50),
#
#             name=permalink,
#             title=title[0:63],
#             description=desc[0:2999],
#
#             url=url,
#
#             hidden=False,
#         )
