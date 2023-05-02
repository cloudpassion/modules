import os
import sys

from logging import Logger, basicConfig

try:
    from config import settings
except ImportError:
    pass

from ..rewrite import (
    Formatter, FULL_FMT, INFO_FMT, MODULE_FMT, DATE_FMT,
    INFO, DEBUG, CRITICAL, ERROR, WARNING,
    StreamHandler,
)
from ..log_colors import ColoredFormatter


# logger for all other modules

if os.name == 'Posix':
    logger_formatter = ColoredFormatter(fmt=INFO_FMT['color'],
                                        datefmt=DATE_FMT['color'], use_color=True)
else:
    logger_formatter = ColoredFormatter(fmt=INFO_FMT['d'],
                                        datefmt=DATE_FMT['d'], use_color=True)

logger_console = StreamHandler(sys.stdout)
logger_console.setFormatter(logger_formatter)
#logger_console.setLevel(INFO)

logger = Logger('logger')
#logger.setLevel(INFO)
while logger.handlers:
    logger.handlers.pop()
logger.addHandler(logger_console)

mlog = logger

# logger for write full log
flogger_formatter = ColoredFormatter(fmt=FULL_FMT['color'], datefmt=DATE_FMT['color'],
                                     use_color=True)
flogger_console = StreamHandler(sys.stderr)
flogger_console.setFormatter(flogger_formatter)
#flogger_console.setLevel(WARNING)

flogger = Logger('full')
#flogger.setLevel(WARNING)
while flogger.handlers:
    flogger.handlers.pop()
flogger.addHandler(flogger_console)


try:
    if settings.log.basic_level:
        basicConfig(
            level=globals()[settings.log.basic_level],
            format=INFO_FMT['d'],
            datefmt=DATE_FMT['d'],
        )
        default_error = False
    else:
        default_error = True

except Exception:
    basicConfig(
        level=10,
        format=INFO_FMT['d'],
        datefmt=DATE_FMT['d'],
    )
    default_error = True

if default_error:
    basicConfig(
        level=ERROR,
        format=INFO_FMT['d'],
        datefmt=DATE_FMT['d'],
    )
