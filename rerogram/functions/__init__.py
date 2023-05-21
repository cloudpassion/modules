from .db import MyPyrogramDbFunctions
from .contacts import MyPyrogramContacts
from .flood import MyPyrogramFlood
from .tests import MyPyroTestFunc

try:
    from .spbportal import MyPyrogramSpbPortal
except ModuleNotFoundError:
    class MyPyrogramSpbPortal:
        pass


class MyPyrogramFunctions(
    MyPyrogramFlood,
    MyPyrogramDbFunctions,
    MyPyrogramContacts,
    MyPyrogramSpbPortal,
    MyPyroTestFunc,
):
    pass
