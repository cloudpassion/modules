from .history import MyPyrogramDbHistory
from .refactor import MyPyrogramDbRefactor


class MyPyrogramDbFunctions(
    MyPyrogramDbRefactor,
    MyPyrogramDbHistory,
):
    pass
