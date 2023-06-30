from .save_update import OuterInitMiddlewareForDispatcher
from .incoming_log import OuterLogForDispatcher


class OuterHandlingForDispatcher(
    OuterInitMiddlewareForDispatcher,
    OuterLogForDispatcher,
):
    pass
