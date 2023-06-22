from .django import (
    MyDjangoORM,
)

from config import settings

__orm__ = {
    'None': None,
    'MyDjangoORM': MyDjangoORM,
}

DbClass = __orm__[getattr(settings.database, 'class')]
