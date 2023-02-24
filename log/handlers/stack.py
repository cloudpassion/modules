import sys
import traceback

from ..rewrite import (
    Formatter, FULL_FMT, DATE_FMT,
    INFO, DEBUG, ERROR, WARNING,
    StreamHandler, Logger, ExcStackLogger,
)
from ..log_colors import ColoredFormatter


def parse_traceback(_trace, _return_text):
    tb_str = traceback.format_exception(
        etype=type(_trace), value=_trace, tb=_trace.__traceback__
    )
    return _return_text + '\n'.join(tb_str)


# log_stack
log_stack_formatter = ColoredFormatter(fmt=FULL_FMT['d'], datefmt=DATE_FMT['d'])

log_stack_console = StreamHandler(sys.stderr)
log_stack_console.setFormatter(log_stack_formatter)
log_stack_console.setLevel(ERROR)

log_stack_file = StreamHandler(sys.stderr)
log_stack_file.setFormatter(log_stack_formatter)
log_stack_file.setLevel(ERROR)

log_stack = ExcStackLogger('main.stack', level=ERROR)
log_stack.setLevel(ERROR)
while log_stack.handlers:
    log_stack.handlers.pop()
log_stack.addHandler(log_stack_console)


test_stack = ExcStackLogger('test_stack', level=ERROR)
while test_stack.handlers:
    test_stack.handlers.pop()
test_stack.setLevel(ERROR)

test_logger = Logger('test_logger', level=INFO)
while test_logger.handlers:
    test_logger.handlers.pop()
test_logger.setLevel(INFO)

