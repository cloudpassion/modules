import django.db.utils
import re
import hashlib
import os
import ujson as json
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors
from datetime import datetime

from typing import Union

from typing import List
from ....django_telegram.django_telegram.datamanager.models import (
    User, Chat, Contact,
    ChatHistory, UserHistory,
    Message, MessageHistory,
    ForwardedToDiscuss,
    SpbPortalProblem, SpbPortalPagePost,
)
from asgiref.sync import sync_to_async, async_to_sync

from atiny.file import create_dirname, create_symlink
from log import log_stack, mlog, logger

from config import settings


GLOBALS = globals()


class DefaultDjangoORM:

    hash_strings = {
        'user': [
            'first_name', 'last_name', 'username', 'phone_number', 'photo',
            'id'
        ],
        'contact': [
            'first_name', 'last_name', 'username', 'phone_number', 'photo',
            'contact_name', 'user',
        ],
        'chat': [
            'title', 'username', 'first_name', 'last_name', 'photo', 'id',
            'type',
        ],
        'message': [
            'text', 'media_ids', 'id', 'reactions', 'poll', 'service',
            'forward_from_message_id', 'reply_to_message_id', 'reply_to_top_message_id',
            'date', 'forward_date',

        ],
        'ForwardedToDiscuss': [
            'message', 'from_message', 'event_message',
            'group_ids', 'post_text',
            'date', 'edit_date',
        ],
        'SpbPortalProblem': [
            'id',
            'text', 'link', 'type', 'status', 'title', 'date', 'category',
            'reason', 'author_name', 'author_id',
        ],
        'SpbPortalPagePost': [
            'post_num', 'title', 'author', 'date', 'text', 'status', 'id',
        ],
    }

    def calc_hash(self, tp, strings, new=None, extra=()):
        _strings = []
        for _string in (*self.hash_strings[tp], *extra):
            try:
                if isinstance(
                        strings[_string], datetime
                ):
                    string = strings[_string].strftime('%s')
                else:
                    string = str(strings[_string])
            except KeyError:
                if new and hasattr(new, _string):
                    string = str(getattr(new, _string))
                else:
                    continue

            _strings.append(string)

        # logger.info(f'{_strings=}')
        hash_object = hashlib.sha512(''.join(_strings).encode('utf8'))
        return hash_object.hexdigest()

    def db_parse_files(
            self,
            force_update=False,
            delete_duplicate_files=False,
            **kwargs
    ):

        file_id, files_md5_list, files_md5 = None, [], None

        if not kwargs.get('files'):
            return

        for f_data in kwargs.get('files'):
            file_id = getattr(f_data, f_data.main_id)
            files_md5_list.append(f_data.md5)

            redownload = False
            try:
                already = f_data.fl_class.objects.filter(
                    md5=f_data.md5,
                ).first()
            except:
                already = False

            try:
                redownload = os.stat(
                    f_data.file_path, follow_symlinks=True
                ).st_size == 0 or (
                        f_data.tg_size and f_data.tg_size != f_data.file_size
                )
            except:
                pass

            if already and not redownload and not f_data.force_update:
                continue

            if f_data.file_data and not f_data.saved:
                create_dirname(f_data.file_path)
                try:
                    f_data.file_data.seek(0)
                    with open(f_data.file_path, 'wb') as fw:
                        fw.write(f_data.file_data.getbuffer())

                    create_symlink(
                        f_data.file_path, f'{f_data.file_dir}{f_data.md5}',
                        _force=True,
                    )
                except:
                    log_stack.error(f'f write file {f_data.file_path}')

            f_data_kwargs = {}
            for key in f_data.db_keys:
                value = getattr(f_data, key)
                if isinstance(
                        value, datetime
                ):
                    f_data_kwargs[key] = int(value.strftime('%s'))
                elif isinstance(value, dict):
                    f_data_kwargs[key] = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, list) and key != 'files':
                    f_data_kwargs[key] = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, set) and key != 'files':
                    f_data_kwargs[key] = json.dumps(
                        list(value), ensuer_ascii=False
                    )
                else:
                    f_data_kwargs[key] = value

            if f_data.unique_id != 'file_unique_id':
                f_data_kwargs['file_unique_id'] = getattr(
                    f_data, f_data.unique_id)
            if f_data.main_id != 'file_id':
                f_data_kwargs['file_id'] = getattr(
                    f_data, f_data.main_id)

            _force_update = False
            if force_update or f_data.force_update:
                new_file = f_data.fl_class.objects.filter(
                    md5=f_data.md5
                ).first()
                if new_file:
                    _force_update = True

                    setattr(
                        new_file, 'path', getattr(f_data, 'file_path')
                    )
                    setattr(
                        new_file, 'size', getattr(f_data, 'file_size')
                    )

                    if f_data.unique_id != 'file_unique_id':
                        setattr(
                            new_file, 'file_unique_id', getattr(
                                f_data, f_data.unique_id)
                        )
                    if f_data.main_id != 'file_id':
                        setattr(
                            new_file, 'file_id', getattr(
                                f_data, f_data.main_id)
                        )
                    for key in f_data.db_keys:
                        setattr(new_file, key, getattr(f_data, key))

                else:
                    new_file = None
                    _force_update = False
            else:
                _force_update = False
                new_file = None

            if not new_file:

                new_file = f_data.fl_class(
                    md5=f_data.md5,
                    size=f_data.file_size,
                    path=f_data.file_path,
                    **{
                        key: f_data_kwargs.get(
                            key
                        ) for key in (
                            'media_group_id',
                            *f_data.db_keys
                        )
                    },
                )

            try:
                new_file.save(force_update=_force_update)
            except errors.lookup(UNIQUE_VIOLATION) as e:
                pass
            except django.db.utils.IntegrityError as exc:
                if 'duplicate key value violates unique constraint' in f'{exc}':
                    pass
                else:
                    log_stack.error(f'integ:')
            except:
                log_stack.error(f'sv file: {f_data.file_path}')

        if files_md5_list:
            files_md5 = ','.join(files_md5_list)

        return file_id, files_md5

    def db_set_one(self, tp, main_id, force_update=False, **kwargs):

        new = globals(
        )[
            f'{(tp[0].upper() + tp[1:])}'
        ].objects.filter(
            **main_id
        ).first()

        # logger.info(f'{main_id=}: {kwargs=}, {(tp[0].upper() + tp[1:])}, {new=}')

        if new:
            for k, v in kwargs.items():
                setattr(new, k, v)
        else:
            force_update = False
            new = globals()[
                f'{(tp[0].upper() + tp[1:])}'
            ](
                **main_id,
                **kwargs,
            )

        db_hash = self.calc_hash(
            tp,
            {
                **main_id,
                **kwargs,
            }, new
        )
        new.hash = db_hash

        try:
            if 'deleted' in kwargs:
                extra_kwargs = {
                    k: v for k, v in kwargs.items() if k != 'deleted'
                }
            else:
                extra_kwargs = kwargs

            extra_tp = f'{(tp[0].upper() + tp[1:])}History'
            if GLOBALS.get(extra_tp):
                extra = GLOBALS[
                    extra_tp
                ](
                    **main_id,
                    **extra_kwargs,
                    hash=db_hash,
                )
            else:
                extra = None
        except KeyError:
            extra = None

        return new, extra, force_update

    # @sync_to_async
    def add_data(
            self, tp: str, add_id: Union[int, dict, None],
            force_insert: bool = False, force_update: bool = False,
            delete_duplicate_files=True,
            **kwargs
    ):
        # logger.info(f'{tp=}, {add_id}, {kwargs=}')

        for key, value in kwargs.copy().items():
            if isinstance(value, datetime):
                kwargs[key] = int(value.strftime('%s'))

            elif isinstance(value, dict):
                kwargs[key] = json.dumps(value, ensure_ascii=False)

            elif key == 'files' and value:
                pass

            elif isinstance(value, list):
                kwargs[key] = json.dumps(value, ensure_ascii=False)

            elif isinstance(value, set) and key != 'files':
                kwargs[key] = json.dumps(list(value), ensure_ascii=False)

        extra, new = None, None

        try:
            file_id, files_md5 = self.db_parse_files(
                force_update=force_update,
                delete_duplicate_files=delete_duplicate_files,
                **kwargs
            )
        except Exception:
            file_id, files_md5 = None, None

        try:
            del kwargs['files']
        except KeyError:
            pass

        try:
            del kwargs['file_id']
        except KeyError:
            pass

        if re.search(
                tp,
                'user,chat,contact'
        ):
            new, extra, force_update = self.db_set_one(
                tp, force_update=force_update,
                main_id={
                            'id': kwargs.get('id'),
                        },
                **{k: v for k, v in kwargs.items() if k != 'id' and k != 'photo'},
                **{
                    'photo': file_id,
                }
            )

        elif tp.lower() == 'message':

            chat = kwargs.get('chat')
            if not chat:
                chat = Chat.objects.filter(id=add_id).first()

            # logger.info(f'{chat=}')
            extra_kwargs = {
                'media_ids': files_md5,
            }
            new, extra, force_update = self.db_set_one(
                tp, force_update=force_update,
                main_id={
                            'id': kwargs.get('id'),
                            'chat': chat,
                        },
                **{k: v for k, v in kwargs.items() if k != 'id' and k != 'chat'},
                **extra_kwargs,
            )

        elif tp == 'ForwardedToDiscuss':
            new, extra, force_update = self.db_set_one(
                tp, force_update=force_update,
                main_id=add_id,
                **{k: v for k, v in kwargs.items()},
            )

        elif tp == 'SpbPortalProblem':
            new, extra, force_update = self.db_set_one(
                tp, force_update=force_update,
                main_id={
                            'id': add_id,
                        },
                **{k: v for k, v in kwargs.items() if k != 'id'},
            )
        elif tp == 'SpbPortalPagePost':
            problem = SpbPortalProblem.objects.filter(
                id=add_id,
            ).first()
            new, extra, force_update = self.db_set_one(
                tp, force_update=force_update,
                main_id={
                    'problem': problem, 'post_num': kwargs.get('post_num')
                },
                **{k: v for k, v in kwargs.items() if k != 'post_num'},
            )

        if extra:
            try:
                extra.save()
            except errors.lookup(UNIQUE_VIOLATION) as e:
                pass
            except django.db.utils.IntegrityError as exc:
                if 'duplicate key value violates unique constraint' in f'{exc}':
                    pass
                else:
                    log_stack.error(f'integ: {tp}')
            except:
                log_stack.error(f'extra')

        if new:
            try:
                new.save(
                    force_update=force_update
                )
            except errors.lookup(UNIQUE_VIOLATION) as e:
                pass
            except django.db.utils.IntegrityError as exc:
                if 'duplicate key value violates unique constraint' in f'{exc}':
                    pass
                else:
                    log_stack.error(f'integ: {tp}')
            except:
                log_stack.error(f'except {add_id=}')

        return new

    def select(self, tp: str, select_id: Union[int, dict], **kwargs):
        try:
            if tp == 'user':
                _select = User.objects.filter(id=select_id).first()
            elif tp == 'contact':
                _select = Contact.objects.filter(id=select_id).first()
            elif tp == 'chat':
                _select = Chat.objects.filter(id=select_id).first()
            # elif tp == 'post':
            #     _select = ChannelPost.objects.filter(
            #         **select_id,
            #     ).first()
            elif tp == 'ForwardedToDiscuss':
                _select = ForwardedToDiscuss.objects.filter(
                    **select_id,
                ).first()
            elif tp == 'SpbPortalProblem':
                _select = SpbPortalProblem.objects.filter(id=select_id).first()
            elif tp == 'SpbPortalPagePost':
                spb_problem = SpbPortalProblem.objects.filter(id=select_id).first()
                logger.info(f'{spb_problem=}')
                _select = SpbPortalPagePost.objects.filter(
                    problem=spb_problem,
                    post_num=kwargs.get('post_num'),
                ).first()
            elif tp[0] == '_':
                # logger.info(f'{select_id=}, {kwargs=}')
                tp = "".join(tp[1:])
                _select = globals()[
                    f'{(tp[0].upper() + tp[1:])}'
                ].objects.filter(
                    **select_id,
                    **kwargs
                ).first()
            elif 'message' in tp:
                chat = Chat.objects.filter(
                    id=select_id
                ).first()
                _select = globals()[
                    f'{(tp[0].upper() + tp[1:])}'
                ].objects.filter(
                    chat=chat,
                    **kwargs
                ).first()
            else:
                logger.info(f'sel else')
                _select = globals()[
                    f'{(tp[0].upper() + tp[1:])}'
                ].objects.filter(
                    **select_id,
                ).first()
        except:
            _select = None
            log_stack.info(f'select: {select_id=}')

        if not _select:
            # logger.info(f'{_select=}, {select_id=}, {kwargs=}')
            return None
            # if tp == 'user':
            #     return User(user_id=int(select_id)).save()
            # elif tp == 'chat':
            #     return Chat(chat_id=int(select_id)).save()

        # for key, value in kwargs.copy().items():
        #     # if isinstance(value, datetime):
        #     #     kwargs[key] = int(value.strftime('%s'))
        #
        #     if isinstance(value, dict):
        #         kwargs[key] = json.dumps(value)
        #
        #     elif key == 'files' and value:
        #         pass
        #         # kwargs['photo'] = value

        return _select

    def select_all(self, tp: str, select_id=None, **kwargs):
        if tp[1] == '_':
            tp = "".join(tp[2:])
            return globals()[
                "".join(tp[0].capitalize() + "".join(tp[1:]))
            ].objects.filter(
                **kwargs
            ).all()
        elif tp[0] == '_':
            tp = "".join(tp[1:])
            if select_id:
                chat = Chat.objects.filter(id=select_id).first()
                return globals()[
                    "".join(tp[0].upper() + "".join(tp[1:]))
                ].objects.filter(
                    chat=chat,
                    **kwargs
                ).all()
            else:
                return globals()[
                    "".join(tp[0].upper() + "".join(tp[1:]))
                ].objects.all()

        elif tp in 'user,chat':
            return globals()[(tp[0].upper() + tp[1:])].objects.all()
        elif 'message' in tp:
            if select_id:
                chat = Chat.objects.filter(id=select_id).first()
                return globals()[
                    (tp[0].upper() + tp[1:])
                ].objects.filter(chat=chat).all()
            else:
                return globals()[(tp[0].upper() + tp[1:])].objects.all()

    # @sync_to_async
    def count_all(self, tp: str):
        if tp == 'user':
            return User.objects.all().count()
        elif tp == 'chat':
            return Chat.objects.all().count()

    # @staticmethod
    # @sync_to_async
    # def add_item(**kwargs):
    #     new_item = Item(**kwargs).save()
    #     return new_item
    #
    # @staticmethod
    # @sync_to_async
    # def get_categories() -> List[Item]:
    #     return Item.objects.distinct("category_name").all()
    #
    # @staticmethod
    # @sync_to_async
    # def get_subcategories(category_code) -> List[Item]:
    #     return Item.objects.distinct("subcategory_name").filter(category_code=category_code).all()
    #
    # @staticmethod
    # @sync_to_async
    # def count_items(category_code, subcategory_code=None) -> int:
    #     conditions = dict(category_code=category_code)
    #     if subcategory_code:
    #         conditions.update(subcategory_code=subcategory_code)
    #
    #     return Item.objects.filter(**conditions).count()
    #
    # @staticmethod
    # @sync_to_async
    # def get_items(category_code, subcategory_code) -> List[Item]:
    #     return Item.objects.filter(category_code=category_code,
    #                                subcategory_code=subcategory_code).all()
    #
    # @staticmethod
    # @sync_to_async
    # def get_item(item_id) -> Item:
    #     return Item.objects.filter(id=int(item_id)).first()
