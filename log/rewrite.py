import os

from logging import (
    DEBUG, CRITICAL, INFO, ERROR, WARNING, NOTSET,
    basicConfig as def_basicConfig, info as def_info,
    StreamHandler, Logger as DefLogger, Formatter, root,
    getLogger
)
import traceback

from collections import defaultdict


INFO_FMT = defaultdict(
    lambda: '[%(asctime)s]f[%(filename)s]f[%(funcName)s]:%(lineno)d | %(message)s',
    {
        'color': '[%(asctime)s]'
                 '%(white)sf'
                 '%(red)s%(bold)s[%(reset)s%(blue)s%(filename)s%(red)s%(bold)s]%(reset)s'
                 '%(white)sf%(yellow)s[%(funcName)s]%(reset)s'
                 ':%(green)s%(lineno)d%(reset)s'
                 ' | '
                 '%(reset)s%(message)s'
    }
)
FULL_FMT = defaultdict(
    lambda: '[%(asctime)s]f[%(filename)s]n[%(name)s]m[%(module)s]i[%(thread)d]' \
            'n[%(threadName)s]p[%(process)d]f[%(funcName)s]' \
            ':%(lineno)d >> %(message)s',
    {
        'color': '[%(asctime)s]f[%(filename)s]n[%(name)s]m[%(module)s]i[%(thread)d]'
                 'n[%(threadName)s]p[%(process)d]f[%(funcName)s]'
                 ':%(lineno)d >> %(message)s'
    }
)
MODULE_FMT = defaultdict(
    lambda: '[%(asctime)s]m[%(module)s]f[%(filename)s]f[%(funcName)s]' \
            ':%(lineno)d %(message)s',
    {
        'color': '[%(asctime)s]m[%(module)s]f[%(filename)s]f[%(funcName)s]'
                 ':%(lineno)d %(message)s'
    }
)

DATE_FMT = defaultdict(
    lambda: '%d.%m %H:%M:%S',
    {
        'color': '%(red)s%d%(white)s.%(reset)s%m %H:%M:%S'
    }
)


# FOR SILENCE OTHER logger MODULE
class SilencableHandler(StreamHandler):

    def __init__(self, *args, **kwargs):
        self.silenced = False
        super(SilencableHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        if not self.silenced:
            return super(SilencableHandler, self).emit(record)


class ExcStackLogger(DefLogger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             stacklevel=1):
        return super(ExcStackLogger, self)._log(
            level, msg, args,
            exc_info=True, extra=None, stack_info=True, stacklevel=stacklevel
        )


class Logger(DefLogger):

    def __init__(self, log_name, *args, **kwargs):
        super().__init__(log_name,  *args, **kwargs)
        # # logger for all other modules
        # formatter = Formatter(fmt=MODULE_FMT, datefmt=DATE_FMT)
        # console = StreamHandler()
        # console.setFormatter(_formatter)
        # console.setLevel(log_level)
        # self.setLevel(log_level)
        # self.addHandler(_console)


def parse_traceback(_trace, _return_text):
    # try:
    #     tb_str = traceback.format_exception(etype=type(_trace), value=_trace, tb=_trace.__traceback__)
    #     return _return_text + '\n'.join(tb_str)
    # except Exception as exc:
    #     # print(f'check exc.ffff:{exc=}')
    #     return 'trace.exc'

    return 'trace.rewrite'


def basicConfig(**kwargs):
    def_basicConfig(**kwargs)


def info(msg, *args, **kwargs):
    def_info(msg, *args, kwargs)

    """
    Log a message with severity 'INFO' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    #if len(root.handlers) == 0:
    #    basicConfig()
    #root.warning(msg, *args, **kwargs)


