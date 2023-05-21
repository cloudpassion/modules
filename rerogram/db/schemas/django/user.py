import django.db.utils

from typing import List
from ....django_telegram.django_telegram.datamanager.models import (
    User,
)
from asgiref.sync import sync_to_async

from log import log_stack, mlog

from .default import DefaultDjangoORM


class DjangoUserORM(DefaultDjangoORM):
    @staticmethod
    @sync_to_async
    def select_user(user_id: int):
        try:
            user = User.objects.filter(user_id=user_id).first()
        except:
            log_stack.info(f'select: {user_id=}')

        mlog.info(f'select: {user=}')

        if not user:
            return User(user_id=int(user_id)).save()

        return user

    @sync_to_async
    def add_user(self, user_id, full_name, username):
        try:
            return User(user_id=int(user_id), name=full_name, username=username).save()
        except django.db.utils.IntegrityError:
            # duplicate key value violates unique constraint "usersmanage_user_user_id_key"
            return User.objects.filter(user_id=user_id).first()
        except Exception:
            log_stack.info(f'except {user_id=}, {full_name=}, {username=}')

    @staticmethod
    @sync_to_async
    def select_all_users():
        users = User.objects.all()
        return users

    @staticmethod
    @sync_to_async
    def count_users():
        return User.objects.all().count()

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
