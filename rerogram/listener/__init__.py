from .forwader import MyPyrogramForwarder
from .monitor import MyPyrogramMonitor


class MyPyrogramListener(
    MyPyrogramForwarder,
    MyPyrogramMonitor,
):
    pass
