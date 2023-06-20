from .django import (
    MyDjangoORM,
)

from config import settings

__db__ = {
    'None': None,
    'MyDjangoORM': MyDjangoORM,
}

DbClass = __db__[getattr(settings.database, 'class')]
