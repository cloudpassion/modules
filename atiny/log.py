import logging
import sys

INFO_FMT = '[%(asctime)s]f[%(filename)s]f[%(funcName)s]:%(lineno)d %(message)s'
FULL_FMT = '[%(asctime)s]f[%(filename)s]n[%(name)s]m[%(module)s]i[%(thread)d]'\
           'n[%(threadName)s]p[%(process)d]f[%(funcName)s]'\
           ':%(lineno)d >> %(message)s'
DATE_FMT = '%m.%d %H:%M:%S'


class ExcStackLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             stacklevel=1):
        return super(ExcStackLogger, self)._log(
            level, msg, args,
            exc_info=True, extra=None, stack_info=True, stacklevel=stacklevel
        )


console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(INFO_FMT, datefmt=DATE_FMT)
console.setFormatter(formatter)

logger = logging.Logger(f'atiny.{__name__}', level=logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(console)

# log_stack
log_stack_formatter = logging.Formatter(fmt=FULL_FMT, datefmt=DATE_FMT)

log_stack_console = logging.StreamHandler(sys.stderr)
log_stack_console.setLevel(logging.ERROR)
log_stack_console.setFormatter(log_stack_formatter)

log_stack = ExcStackLogger('atiny.stack', level=logging.ERROR)
log_stack.setLevel(logging.ERROR)
log_stack.addHandler(log_stack_console)


def basic_debug():
    logging.basicConfig(
        level=logging.DEBUG,
        format=FULL_FMT,
        datefmt=DATE_FMT,
    )


def parse_traceback(_trace, _return_text):
    # try:
    #     tb_str = traceback.format_exception(etype=type(_trace), value=_trace, tb=_trace.__traceback__)
    #     return _return_text + '\n'.join(tb_str)
    # except Exception as exc:
    #     # print(f'check exc.ffff:{exc=}')
    #     return 'trace.exc'

    return 'trace.rewrite'


# logging.basicConfig(
#     level=logging.WARNING,
#     format=INFO_FMT,
#     datefmt=DATE_FMT,
# )
