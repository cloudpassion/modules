import asyncio
import re
import pyrogram
import string
import itertools
import ujson as json

from datetime import datetime
from pyrogram.errors.exceptions.flood_420 import FloodWait
from collections import deque

from pyrogram.raw.functions.contacts import AddContact, ResolvePhone
from pyrogram import Client as PyrogramClient
from pyrogram.types import (
    Message as PyrogramMessage, InputPhoneContact,
)
from pyrogram.raw.types import InputUserEmpty

from rerogram.client import MyAbstractTelegramClient
from ..db.types.message import MyEventMessageDatabase

try:
    from phones import PhoneSearch
except ImportError:
    pass

from config import settings
from log import logger, log_stack


class MyPyrogramContacts(
    MyAbstractTelegramClient,
    PyrogramClient
):

    async def get_admins(self, chat_id):
        async for member in self.get_chat_members(
                chat_id,
                filter=pyrogram.enums.ChatMembersFilter.ADMINISTRATORS
        ):
            logger.info(f'admin: {member=}')

    async def get_bots(self, chat_id):
        async for member in self.get_chat_members(
                chat_id,
                filter=pyrogram.enums.ChatMembersFilter.BOTS
        ):
            logger.info(f'{member=}')

    async def get_members(self, chat_id):
        members = {}
        async for member in self.get_chat_members(
                chat_id
        ):
            members[member.user.id] = member

        return members

    async def query_find_ignore(self, from_chat_ids, query):

        if not query:
            return

        for chat_id in from_chat_ids:
            async for message in self.search_messages(
                    chat_id, limit=5, query=query,
            ):
                logger.info(f'{message=}')
                member = message.from_user
                hint_name = f'{member.first_name}' \
                            f'{" " if member.last_name else ""}' \
                            f'{member.last_name if member.last_name else ""}' \
                            f'{" @" if member.username else ""}' \
                            f'{member.username if member.username else ""}'

                logger.info({message.from_user.id: {'name': hint_name}})

    async def query_user_find_ignore(self, from_chat_ids, query):

        for chat_id in from_chat_ids:
            async for member in self.get_chat_members(
                    chat_id, query=query.lower()
            ):
                hint_name = f'{member.user.first_name}' \
                            f'{" " if member.user.last_name else ""}' \
                            f'{member.user.last_name if member.user.last_name else ""}' \
                            f'{" @" if member.user.username else ""}' \
                            f'{member.user.username if member.user.username else ""}'

                logger.info(f'{member=}')
                logger.info({member.user.id: {'name': hint_name,}})

    async def contacts_find_ignore(self, from_chat_ids, names, skip_ids):
        finded = set()
        finded_data = {}
        notfinded = set()

        logger.info(f'{names=}, {from_chat_ids=}')
        for chat_id in from_chat_ids:

            async for member in self.get_chat_members(
                    chat_id
            ):

                hint_name = f'{member.user.first_name}' \
                       f'{" " if member.user.last_name else ""}' \
                       f'{member.user.last_name if member.user.last_name else ""}' \
                       f'{" @" if member.user.username else ""}' \
                       f'{member.user.username if member.user.username else ""}'

                sms = None
                async for message in self.search_messages(
                    chat_id, from_user=member.user.id, limit=1,
                ):
                    sms = f'{message.from_user.first_name}: {message.text=}'

                for name in names:
                    if name.lower() in hint_name.lower():
                        if member.user.id in skip_ids:
                            continue

                        finded_data[member.user.id] = {
                            'name': hint_name, 'sms': sms
                        }
                        finded.add(name)

        for name in names:
            if name not in finded:
                notfinded.add(name)

        logger.info(f'{notfinded=}')
        logger.info(f'{finded=}')
        logger.info(f'{finded_data=}')

        return finded

    async def add_all_to_contact(self, chat_id):

        letters = deque()
        letters.extend(list(string.ascii_uppercase))
        letters.extend(list(string.ascii_lowercase))
        letters.extend(list(string.digits))
        alphabets = ''.join(letters)
        keywords = [''.join(i) for i in itertools.product(alphabets, repeat=2)]

        letters.extend(keywords)

        chat = await self.get_chat(chat_id)

        async for member in self.get_chat_members(chat_id):

            if member.user.is_contact:
                continue

            await self.user_database(
                member.user, client=self, message=None, log=False
            )

            if member.user.is_self:
                continue

            logger.info(f'{member=}')
            name = f'{member.user.first_name}' \
                   f'{" " if member.user.last_name else ""}' \
                   f'{member.user.last_name if member.user.last_name else ""}' \
                   f'{" @" if member.user.username else ""}' \
                   f'{member.user.username if member.user.username else ""}'

            # name = f'letters.popleft()
            user = await self.db.select(
                'user', member.user.id
            )
            contact = await self.db.select(
                'contact', user
            )

            if contact:
                from_chat_names = set(json.loads(contact.from_chat_names))
                from_chat_ids = set(json.loads(contact.from_chat_ids))
                notify_ignore = contact.notify_ignore
                add_ignore = contact.add_ignore
                pm_ignore = contact.pm_ignore
            else:
                from_chat_names = set()
                from_chat_ids = set()
                notify_ignore = False
                add_ignore = False
                pm_ignore = False

            hint_name = f'{member.user.first_name}' \
                        f'{" " if member.user.last_name else ""}' \
                        f'{member.user.last_name if member.user.last_name else ""}' \
                        f'{" @" if member.user.username else ""}' \
                        f'{member.user.username if member.user.username else ""}'

            from_chat_ids.add(chat.id)
            from_chat_names.add(chat.title)

            self.db.add_data(
                'contact',
                add_id=user, hint_name=hint_name,
                contact_name=name,
                from_chat_names=from_chat_names,
                from_chat_ids=from_chat_ids,
                notify_ignore=notify_ignore,
                add_ignore=add_ignore,
                pm_ignore=pm_ignore,
            )

            while True:
                try:
                    await self.add_contact(
                        member.user.id, first_name=name,
                        share_phone_number=False,
                    )
                    break
                except FloodWait as _exc:
                    logger.info(f'{_exc=}')
                    exc = f'{_exc}'
                    wait_time = int(re.findall('A wait of (.*?) seconds', exc)[0])
                    while wait_time > 0:
                        logger.info(f'{wait_time=}')
                        await asyncio.sleep(30)
                        wait_time -= 30

    async def notify_test(
        self, send_chat_id, user_ids,
    ):
        _user_ids = user_ids.copy()

        text = deque('''
            

this is text
        ''')

        offset = 0
        entities = []
        bolds = (
        )
        underlines = (
        )
        entity_text = ''
        users = {}

        while True:

            try:
                user_id = user_ids.pop()
            except IndexError:
                user_ids = _user_ids.copy()
                user_id = user_ids.pop()

            if user_id in users:
                user = users[user_id]
            else:
                user = (await self.get_users(user_ids=[user_id, ]))[0]
                users[user.id] = user

            try:
                word = text.popleft()
                len_word = len(word)
                if re.search('\n| ', word):
                    pass
                else:
                    entity = pyrogram.types.MessageEntity(
                        type=pyrogram.enums.MessageEntityType.TEXT_MENTION,
                        offset=offset, length=len_word,
                        user=user
                    )
                    entities.append(entity)
            except IndexError:
                break

            # if len(entities) >= 50:
            #     break

            offset += len_word
            entity_text += word

        await self.send_message(
            send_chat_id, text=entity_text+''.join(text), entities=entities,
        )
        for n, entity in enumerate(entities):
            logger.info(f'{n=}, {entity=}')

    async def insert_user_to_entities(
            self, entity_offsets, users, contacts, user_ids,
            skip_user_ids, of_chat_id, text_entities,
            user_ids_count,
            of_chat_members, not_of_chat_members,
    ):

        count_entities = 0
        big_entities = []

        if user_ids:
            _user_ids = user_ids.copy()

        while True:

            entities = []
            _entity_offsets = entity_offsets.copy()
            while _entity_offsets:

                try:
                    _data = _entity_offsets.popleft()
                except ValueError:
                    break

                entity_offset = _data[0]
                entity_len_word = _data[1]

                if user_ids or users:
                    try:
                        user_id = user_ids.pop()
                    except IndexError:
                        user_ids = _user_ids.copy()
                        user_id = user_ids.pop()

                    if user_id in users:
                        user = users[user_id]
                    else:
                        user = (await self.get_users(user_ids=[user_id, ]))[0]
                        users[user.id] = user

                else:
                    try:
                        user = contacts.popleft()
                    except IndexError:
                        break

                    if user.id in skip_user_ids:
                        _entity_offsets.appendleft(_data)
                        continue

                    if user.is_self:
                        if user.is_contact:
                            await self.delete_contacts([user.id, ])
                        _entity_offsets.appendleft(_data)
                        continue

                    if of_chat_id:
                        if user.id not in of_chat_members:
                            _entity_offsets.appendleft(_data)
                            continue
                        if user.id in not_of_chat_members:
                            _entity_offsets.appendleft(_data)
                            continue

                count_entities += 1
                entity = pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.TEXT_MENTION,
                    offset=entity_offset, length=entity_len_word,
                    user=user
                )
                entities.append(entity)
                if len(entities)+len(text_entities) >= 100:
                    break

            if entities:
                big_entities.append([
                    *entities,
                    *text_entities
                ])

            if user_ids or users:
                if count_entities >= user_ids_count:
                    break
            else:
                if not contacts:
                    break

        return count_entities, big_entities

    async def notify_all_contacts_new(
            self, send_chat_id, text,
            of_chat_id=False, not_of_chat_id=None,
            skip_user_ids=None, bolds=[], underlines=[],
            user_ids=None, user_ids_count=600,
    ):

        users = {}
        _text = text.copy()

        if of_chat_id:
            of_chat_members = await self.get_members(of_chat_id)
        else:
            of_chat_members = None

        if not_of_chat_id:
            not_of_chat_members = await self.get_members(not_of_chat_id)
        else:
            not_of_chat_members = None

        if not user_ids:
            try:
                contacts = deque(await self.get_contacts())
            except:
                _contacts = await self.get_members(of_chat_id)
                contacts = deque([x.user for x in _contacts.values()])
        else:
            contacts = None

        text_entities, added_offset = await self.add_entites(
            "".join(text), bolds=bolds, underlines=underlines,
        )

        entity_text = ''

        offset = 0
        entity_offsets = deque()
        while True:

            try:
                word = text.popleft()
                len_word = len(word)
                if re.search('\n| ', word):
                    pass
                else:
                    if offset in added_offset:
                        pass
                    else:
                        entity_offsets.append(
                            (offset, len_word)
                        )
            except IndexError:
                break

            offset += len_word
            entity_text += word

        count_entities, big_entities = await self.insert_user_to_entities(
            entity_offsets=entity_offsets, users=users, contacts=contacts,
            user_ids=user_ids, skip_user_ids=skip_user_ids,
            of_chat_id=of_chat_id, text_entities=text_entities,
            user_ids_count=user_ids_count, of_chat_members=of_chat_members,
            not_of_chat_member=not_of_chat_members
        )

        extra_entities = []
        for big_entity in big_entities:
            _msg = await self.send_message(
                send_chat_id, text=entity_text, entities=big_entity,
            )

            for entity in big_entity:
                if entity.type != pyrogram.enums.MessageEntityType.TEXT_MENTION:
                    continue

                if entity not in _msg.entities:
                    logger.info(f'{entity=} not in 1')
                    extra_entities.append(entity)

            logger.info(f'{len(big_entity)}')
            logger.info(f'{len(_msg.entities)=}')

        logger.info(f'e{len(extra_entities)=}')

        extra_text = '\n'
        extra_users = deque()
        for entity in extra_entities:
            if entity.user.username:
                extra_text += f'@{entity.user.username} '
            else:
                extra_users.append(entity.user)

        _msg = await self.send_message(
            send_chat_id, text="".join(_text)+extra_text, entities=text_entities,
        )
        logger.info(f'{len(_msg.entities)=}')

        # count_entities, big_entities = await self.insert_user_to_entities(
        #     entity_offsets=entity_offsets, users=users, contacts=extra_users,
        #     user_ids=user_ids, skip_user_ids=skip_user_ids,
        #     of_chat_id=of_chat_id, text_entities=text_entities,
        #     user_ids_count=user_ids_count, chat_members=chat_members,
        # )
        #
        # next_entities = []
        # for big_entity in big_entities:
        #     _msg = await self.send_message(
        #         send_chat_id, text=entity_text, entities=big_entity,
        #     )
        #
        #     for entity in big_entity:
        #         if entity.type != pyrogram.enums.MessageEntityType.TEXT_MENTION:
        #             continue
        #
        #         if entity not in _msg.entities:
        #             logger.info(f'{entity=} not in 1')
        #             next_entities.append(entity)
        #
        #     logger.info(f'{len(big_entity)}')
        #     logger.info(f'{len(_msg.entities)=}')
        #
        # logger.info(f'e{len(next_entities)=}')

        chat = await self.get_chat(of_chat_id)
        logger.info(f'{count_entities=}')
        logger.info(f'{chat.members_count=}')
        if of_chat_id:
            logger.info(f'{len(of_chat_members)}')

        #
        # for n, entity in enumerate(entities):
        #     logger.info(f'{n=}, {entity=}')
        #
        # logger.info(f'{len(entities)=}')

    async def notify_all_contacts(
            self, send_chat_id, of_chat_id=False,
            skip_user_ids=None
    ):

        if of_chat_id:
            chat_members = await self.get_members(of_chat_id)

        contacts = deque(await self.get_contacts())
        logger.info(f'{len(contacts)=}')
        qw = False

        while True:

            entity_text = deque('''
            
''')
            text = '''

'''

#             entity_text = deque('''
# ''')

            entities = []
            bolds = (
            )
            underlines = (
            )

            for bold in bolds:
                try:
                    letter_index = text.lower().index(bold.lower())
                except ValueError:
                    logger.info(f'{bold=}')
                    continue

                entity = pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.BOLD,
                    offset=letter_index, length=len(bold)+1,
                )
                entities.append(entity)

            for underline in underlines:
                try:
                    letter_index = text.lower().index(underline.lower())
                except ValueError:
                    logger.info(f'{underline=}')
                    continue

                entity = pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.PHONE_NUMBER,
                    offset=letter_index, length=len(underline)+1,
                )
                entities.append(entity)

            offset = len(text) + 1

            while True:

                if not contacts:
                    qw = True
                    break

                if len(text) + 1 + len("".join(entity_text)) >= 4096:
                    logger.info(f'break sym')
                    break

                contact = contacts.popleft()
                if contact.id in skip_user_ids:
                    continue

                if contact.is_self:
                    if contact.is_contact:
                        await self.delete_contacts([contact.id, ])
                    continue

                if of_chat_id:
                    if contact.id not in chat_members:
                        continue

                if entity_text:
                    word = entity_text.popleft()
                elif extra_entity_text:
                    word = extra_entity_text.popleft()
                else:
                    extra_entity_text = deque('ТУ')
                    word = extra_entity_text.popleft()

                len_word = len(word)

                entity = pyrogram.types.MessageEntity(
                    type=pyrogram.enums.MessageEntityType.TEXT_MENTION,
                    offset=offset, length=len_word,
                    user=contact
                )
                entities.append(entity)

                if len(entities) >= 50:
                    logger.info(f'break 50')
                    qw = True
                    break

                offset += len_word
                text += word

            logger.info(f'{len(entities)=}')
            await self.send_message(
                send_chat_id, text=text+''.join(entity_text), entities=entities,
            )
            for n, entity in enumerate(entities):
                logger.info(f'{n=}, {entity=}')

            if qw:
                break

    async def parse_and_add_contact_by_user(
            self, name, user_id, text='', path=None,
            checked=None, dir_path=None,
    ):

        if not text and not path and not dir_path:
            return

        phones = PhoneSearch().file_get_contacts(path)
        # phones = PhoneSearch().file_xls_yandex(path)
        # phones = PhoneSearch().dir_xls_latitude(
        #     dir_path=dir_path,
        #     center=[60.072027, 30.318500],
        #     radius=2,
        # )

        contacts = await self.get_contacts()
        if not user_id:
            for contact in contacts:
                if name in f'{contact.first_name} ' \
                           f'{contact.last_name} ' \
                           f'{contact.username}':
                    logger.info(f'{contact=}')

            quit()
        # for x in contacts:
        #     if 'bulba' in x.first_name:
        #         logger.info(f'{x=}')
        #         quit()
        #
        # quit()

        cur_phones = {x.phone_number: x for x in contacts}

        if checked:
            checked_file = checked
            with open(checked, 'r') as rc:
                checked = set([x.splitlines()[0] for x in rc.readlines()])
        else:
            checked_file = f'/home/mg/work/my/stuff/phones/' \
                           f'checked.{name}.txt'
            checked = set()

        if not phones:
            return

        logger.info(f'{len(phones)}')
        # return
        try:
            for n, phone in enumerate(phones):
                if phone in checked:
                    continue

                if phone in cur_phones:
                    logger.info(f'exists {name} {n} {phone}. '
                                f'{cur_phones[phone].first_name}')
                    continue

                while True:
                    try:
                        user = await self.add_contact(
                            user_id=user_id,
                            first_name=f'{name} {n} {phone}',
                            phone_number=phone,
                        )
                        break
                    except FloodWait as exc:
                        await self.parse_flood('cnt_add', exc)
                        if checked:
                            with open(checked_file, 'a') as ca:
                                ca.write('\n'.join(checked)+'\n')
                        checked = set()

                logger.info(f'{user.first_name=}')
                if not user.phone_number:
                    while True:
                        try:
                            await self.delete_contacts(
                                user_ids=[user_id, ]
                            )
                            break
                        except FloodWait as exc:
                            await self.parse_flood('cnt_del', exc)

                            if checked:
                                with open(checked_file, 'a') as ca:
                                    ca.write('\n'.join(checked)+'\n')
                            checked = set()

                else:
                    logger.info(f'FOUND: {user=}')
                    break

                checked.add(phone)

        except KeyboardInterrupt:
            with open(f'/home/mg/checked.txt', 'a') as ca:
                ca.write('\n'.join(checked))

            checked = None
        except Exception:
            log_stack.error(f'stack')

        logger.info(f'{checked_file=}')
        if checked:
            with open(checked_file, 'a') as ca:
                ca.write('\n'.join(checked))

    async def parse_and_add_contacts_resolve(self, name, text='', path=None):
        if not text and not path:
            return

        phones = PhoneSearch().file_get_contacts(path)

        contacts = await self.get_contacts()
        cur_phones = [x.phone_number for x in contacts]

        new_contacts = []

        for n, phone in enumerate(phones):
            if phone in cur_phones:
                logger.info(f'exists {name} {n} {phone}')
                continue

            logger.info(f'add {name} {n} {phone}')
            new_contacts.append(
                InputPhoneContact(phone, f'{name} {n}')
            )

            next_phone = False
            while True:
                try:
                    user = await self.invoke(
                        ResolvePhone(
                            phone=phone
                        )
                    )
                    break
                except FloodWait as exc:
                    await self.parse_flood('rsv_phone', exc)
                except Exception as exc:
                    logger.info(f'{exc=}')
                    if 'PHONE_NOT_OCCUPIED' in f'{exc}':
                        next_phone = True
                        break
                    else:
                        await asyncio.sleep(60)

            if next_phone:
                continue

            if user:
                res = await self.add_contact(
                    user_id=user.peer.user_id,
                    first_name=f'{name} {n}', phone_number=phone,
                )
                logger.info(f'{res=}')

            await asyncio.sleep(2)

        # while new_contacts:
        #     c = 10
        #     to_add = []
        #     while new_contacts and c:
        #         try:
        #             to_add.append(new_contacts.pop)
        #         except IndexError:
        #             break
        #         c -= 1
        #
        #     logger.info(f'{len(to_add)}')
        #     res = await self.import_contacts(new_contacts)
        #     logger.info(f'{res=}')
        #     await asyncio.sleep(60)







