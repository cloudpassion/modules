from .chat import DjangoChatORM
from .user import DjangoUserORM


class MyDjangoORM(
    DjangoChatORM,
    DjangoUserORM
):
    pass
