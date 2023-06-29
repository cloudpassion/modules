from .types import PyrogramMessage


class MergedPyrogramMessage:

    init_message: PyrogramMessage
    # async def load_parse_functions(self):
    #     self.db_parse_functions = {
    #         f'pyrogram_{k}': for k, v in (
    #         self.
    #     )
    #     }

    async def _merge_pyrogram_message(self):
        return self.init_message

        if not delete:
            for _chat in ('chat', 'sender_chat', 'forward_from_chat'):
                if not hasattr(message, _chat):
                    continue
                _chat_ = await self.database_chat(
                    chat=getattr(message, _chat),
                )
                setattr(message, f'_{_chat}', _chat_)
            for _user in ('forward_from', 'from_user'):
                if not hasattr(message, _user):
                    continue

                _user_ = await self.database_user(
                    user=getattr(message, _user),
                )
                setattr(message, f'_{_user}', _user_)

        elif delete:
            async def _add_group_ids(_db_check, _delete_data):

                if not _delete_data.get(_db_check.chat.id):
                    _delete_data[_db_check.chat.id] = []

                _m_group_ids = json.loads(
                    _db_check.media_group_ids
                ) if _db_check.media_group_ids else []

                for _group_id in _m_group_ids:
                    _delete_data[_db_check.chat.id].append(_group_id)

                if not _m_group_ids:
                    _delete_data[_db_check.chat.id].append(_db_check.id)

                return _delete_data

            delete_data = {}
            for _message in message:

                ids = [_message.id, ]
                try:
                    db_check = self.orm.select(
                        'message',
                        _message.chat.id,
                        id=_message.id,
                    )
                # if delete in self chat
                except AttributeError:
                    continue

                if not db_check:
                    continue

                db_discuss = db_check.discuss_message
                if db_discuss:
                    delete_data = await _add_group_ids(db_discuss, delete_data)

                delete_data = await _add_group_ids(db_check, delete_data)

            for g_id, d_messages in delete_data.items():

                for d_msg in d_messages:
                    db_check = self.orm.select(
                        'message',
                        g_id,
                        id=d_msg,
                    )
                    if not db_check:
                        continue

                    add_data = self.orm.add_data(
                        'message',
                        add_id=g_id,
                        id=d_msg,
                        deleted=True, force_update=True,
                        edit_date=datetime.now()
                    )

            return

        db_check = self.orm.select(
            'message',
            message.chat.id,
            id=message.id
        )
        logger.info(f'{message.id=}, {db_check=}')

        if check:
            return db_check

        # TODO: remake to any
        skip_chats = settings.database.skip
        for _id in skip_chats:
            if message.chat and message.chat.id == _id:
                return 'skip'

        deleted = delete

        db_keys_message = (
            'id', 'text', 'caption',
            'date', 'forward_date',
            'media_group_id',
            'from_id',
            'reply_to_top_message_id', 'reply_to_message_id',
            'discuss_message', 'views', 'forward_from_message_id',
        )
        db_models_message = (
            'from_user', 'forward_from', 'forward_from_chat',
            'sender_chat', 'forward_from_chat'
        )
        keys_message = (
            'service', 'edit_date',
        )
        db_keys_locals = (
            'edit_date', 'db_date', 'entities', 'poll', 'files', 'reactions',
            'service', 'deleted', 'media_group_ids',
        )

        for k in (*db_keys_message, *keys_message, *db_models_message):
            if not hasattr(message, k):
                setattr(message, k, None)

        message.from_id = message.from_user.id if message.from_user else (
            message.sender_chat.id
        ) if message.sender_chat else None

        media_group_ids = []
        _media_messages = [] if not _media_messages else _media_messages
        if message.media_group_id:
            media_group_ids = []
            _media_group_ids = json.loads(
                db_check.media_group_ids
            ) if db_check and db_check.media_group_ids else []

            if _media_group_ids:
                media_group_ids = _media_group_ids
                if not _media_messages:
                    _media_messages = await self.get_media_group_db(
                        message.chat.id,
                        media_group_id=message.media_group_id,
                        # net=True if not db_check else False,
                    )

            if not media_group_ids:
                if not _media_messages:
                    _media_messages = await self.get_media_group_db(
                        message.chat.id,
                        message.id,
                        # net=True if not db_check else False,
                    )
                media_group_ids = [x.id for x in _media_messages]

        _media_messages.sort(key=lambda x: x.id, reverse=False)
        media_group_ids.sort(key=lambda x: x, reverse=False)

        # logger.info(f'{message.media_group_id=}, '
        #             f'{db_check.media_group_id if db_check else None}\n'
        #             f'{db_check.media_group_ids if db_check else None},'
        #             f'{media_group_ids=}')

        if False and message.chat.type != pyrogram.enums.ChatType.CHANNEL:
            pass
            # if message.sender_chat:
            #     if message.media_group_id:
            #         if self.database_skip_media_group[message.media_group_id]:
            #             _media_group_messages = self.database_skip_media_group[message.media_group_id]
            #         else:
            #             _media_group_messages = await self.get_media_group(
            #                 message.chat.id, message.id
            #             )
            #         msg_group = list(_media_group_messages)
            #         # msg_group.sort(key=lambda x: x.id, reverse=False)
            #     else:
            #         msg_group = [message, ]
            #
            #     logger.info(f'{message.id=}, {[x.id for x in msg_group]=}')
            #
            #     db_discuss = None
            #     for msg in msg_group:
            #
            #         db_msg = self.orn.select(
            #             'message',
            #             msg.chat.id,
            #             id=msg.id,
            #         )
            #         logger.info(f'group: {msg.id=}, {db_msg=}')
            #         if db_msg:
            #             db_discuss = self.orm.select(
            #                 '_message',
            #                 {
            #                     'discuss_message': db_msg
            #                 }
            #             )
            #
            #         if db_discuss:
            #             break
            #
            #         reply = None
            #         while True:
            #             try:
            #                 async for reply in self.get_discussion_replies(
            #                     chat_id=msg.chat.id,
            #                     message_id=msg.id,
            #                     limit=1
            #                 ):
            #                     pass
            #                 break
            #             except FloodWait as exc:
            #                 await self.parse_flood('chat_reply', exc)
            #             except Exception as exc:
            #                 await self.parse_flood('chat_reply', exc, wait=False)
            #                 break
            #
            #         if reply:
            #             messages = await self.get_messages(
            #                 msg.forward_from_chat.id,
            #                 message_ids=[msg.forward_from_message_id, ]
            #             )
            #             logger.info(f'{messages=}')
            #             db_try = await self.database_message(
            #                 message=messages[0]
            #             )
            #             logger.info(f'{db_try=}')
            #             while True:
            #                 await asyncio.sleep(0.1)
            #
            #         while True:
            #             await asyncio.sleep(0.1)
            #         # replies = await self.get_discussion_replies(
            #         #
            #         # )
            #         # replies = await self.invoke(
            #         #     GetReplies(
            #         #         peer=message.chat,
            #         #         msg_id=message.chat.id,
            #         #         limit=1
            #         #     )
            #         # )
            #         # logger.info(f'{replies=}')
            #         # quit()

        elif message.chat.type == pyrogram.enums.ChatType.CHANNEL and message.sender_chat:

            if message.service:
                pass
            else:

                chat_msg = None
                logger.info(f'{media_group_ids=}, {message.id=}')
                if media_group_ids and message.id != media_group_ids[0]:
                    chat_msg = True

                while not chat_msg:
                    try:
                        chat_msg = await self.get_discussion_message(
                            message.chat.id, message.id,
                        )
                        if not chat_msg:
                            break

                        logger.info(f'{chat_msg.id=}, {message.id=}')
                        while True:
                            db_msg = await self.database_message(
                                message=chat_msg,
                            )
                            if db_msg:
                                break

                            await asyncio.sleep(0.1)
                            logger.info(f'sl_dm')

                        logger.info(f'{chat_msg.id=}, {message.id=}, '
                                    f'{db_msg.id=}')
                        message.discuss_message = db_msg
                        break
                    except FloodWait as exc:
                        await self.parse_flood(f'chat_msg.{message.id=}', exc)
                    except Exception as exc:
                        # log_stack.error(f'ch_dis_msg')
                        logger.info(f'ch_dis_msg')
                        break

        db_date = datetime.now()
        edit_date = message.edit_date

        files = await self.parse_files(
            message,
        )
        reactions = await self.parse_reactions(
            message,
        )
        poll = self.parse_poll(
            message,
        )
        service = await self._message_parse_service(
            message,
        )

        _entities = message.entities

        entities = []
        if _entities:
            for entity in _entities:
                if entity.type == pyrogram.enums.MessageEntityType.SPOILER:
                    entities.append(
                        f'spoiler_{entity.offset}_{entity.length}'
                    )
                else:
                    entities.append(
                        f'other_{entity.offset}_{entity.length}'
                    )

        _locals = locals()
        add_data = self.orm.add_data(
            'message',
            add_id=message.chat.id,
            # this line first, because id=
            **{k: getattr(message, k) for k in (*db_keys_message, )},
            # next
            **{k: getattr(message, f'_{k}') for k in db_models_message},
            **{k: _locals[k] for k in (*db_keys_locals, )},
            force_update=True,
        )

        while True:
            if add_data:
                break

            await asyncio.sleep(0.1)
            logger.info(f'f{add_data=}')

        if message.media_group_id:

            while True and not _media_messages:
                if not _media_messages:
                    _media_messages = await self.get_media_group_db(
                        message.chat.id,
                        media_group_id=message.media_group_id,
                    )

                logger.info(f'{[x.id for x in _media_messages]=}')
                if _media_messages:
                    break

                logger.info(f'sl_m')
                await asyncio.sleep(0.1)

            if message.id == _media_messages[0].id:

                parsed = []
                new_msg = []
                data = {}

                for msg in [
                    x for x in _media_messages if x.id != message.id
                ]:
                    if isinstance(msg, DjangoTelegramMessage):
                        continue

                    done, pending = await asyncio.wait(
                        [self.database_message(
                            msg, delete=False,
                            _media_messages=_media_messages,
                        ), ],
                        return_when=asyncio.ALL_COMPLETED,
                    )

                    logger.info(f'was1.1: {pending=}, {done=}')
                    while pending:
                        await asyncio.sleep(0.1)
                        logger.info(f'was2.2: {pending=}, {done=}')

                    _msg = list(done)[0].result()
                    parsed.append(_msg)

                # if parsed:
                #     parsed.sort(key=lambda x: x.id, reverse=False)
                # logger.info(f'{[x for x in parsed]=}')
                #     return parsed[0]
                #
                # return 'next'

        return add_data

    async def _message_parse_service(
            self,
            message: MESSAGE_TYPES,
    ):

        if not message.service:
            return

        _service = message.service
        service_type = SERVICE_TYPES[message.service]

        if _service == pyrogram.enums.MessageServiceType.NEW_CHAT_MEMBERS:
            service_data = {
                'user_ids': [x.id for x in message.new_chat_members]
            }

            for user in message.new_chat_members:
                await self.database_user(
                    user=user,
                )
        elif _service == pyrogram.enums.MessageServiceType.LEFT_CHAT_MEMBERS:
            service_data = {
                'user_id': message.left_chat_member.id
            }
            await self.database_user(
                user=message.left_chat_member,
            )
        elif _service == pyrogram.enums.MessageServiceType.PINNED_MESSAGE:
            service_data = {
                'message_id': message.pinned_message.id
            }
        elif _service == pyrogram.enums.MessageServiceType.CHANNEL_CHAT_CREATED:
            return None
        else:
            logger.info(f'new_type: {message=}')
            return None

        return {'type': service_type, 'data': service_data}

    def parse_poll(
            self,
            message: Union[
                PyrogramMessage, DjangoTelegramMessage, None,
            ],
            raw_data: pyrogram.types.Poll = None,
    ):
        if message and not getattr(message, 'poll') and not message.poll:
            return

        if raw_data:
            poll_id = raw_data.id

        if message:
            poll_id = message.poll.id

        new = DjangoTelegramPoll.objects.filter(id=poll_id).first()

        if raw_data and not new:
            return

        if message:
            poll_dict = {}
            poll = message.poll
            question = poll.question
            total_voter_count = poll.total_voter_count
            is_closed = poll.is_closed
            is_anonymous = poll.is_anonymous
            allow_multiple_answers = poll.allows_multiple_answers
            poll_type = POLL_TYPES[poll.type]
            options = poll.options

            poll_dict.update({
                'id': poll_id, 'question': question, 'total_voter_count': total_voter_count,
                'is_closed': is_closed, 'is_anonymous': is_anonymous,
                'allow_multiple_answers': allow_multiple_answers,
                'count': len(options), 'type': poll_type,
            })

            for n, opt in enumerate(poll.options):
                opt_text = opt.text
                voter_count = opt.voter_count
                opt_data = opt.data
                opt_json = {
                    'text': opt_text, 'voter_count': voter_count,
                    'data': hashlib.sha512(opt_data).hexdigest(),
                }
                poll_dict[n] = opt_json

            poll_options = {k: poll_dict[k] for k in range(0, poll_dict['count'])}

        else:
            total_voter_count = raw_data.total_voter_count
            poll_options = {
                n: {
                    'text': option.text,
                    'voter_count': option.voter_count,
                    'data': hashlib.sha512(option.data).hexdigest(),
                } for n, option in enumerate(raw_data.options)
            }

        if new:
            _force_update = True
            setattr(new, 'total_voter_count', total_voter_count)
            setattr(new, 'options', poll_options)
            if message:
                setattr(new, 'poll_id', poll_id)
                setattr(new, 'question', question)
                setattr(new, 'is_closed', is_closed)
                setattr(new, 'is_anonymous', is_anonymous)
                setattr(new, 'allow_multiple_answers', allow_multiple_answers)
                setattr(new, 'type', poll_type)
        else:
            _force_update = False
            new = DjangoTelegramPoll(
                id=poll_id, question=question,
                total_voter_count=total_voter_count, is_closed=is_closed,
                is_anonymous=is_anonymous,
                allow_multiple_answers=allow_multiple_answers,
                type=poll_type,
                options=poll_options,
            )

        new.save(force_update=_force_update)
        return new

