from ..db.schemas.django import (
    MyDjangoORM,
)

from config import settings, secrets

__db__ = {
    'None': None,
    'MyDjangoORM': MyDjangoORM(),
}

SqlDatabase = __db__[settings.database.database]
