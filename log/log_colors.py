import logging
import time
import re

from .const.log_colors import ALL_COLORS
# https://stackoverflow.com/a/384125

#The background is set with 40 plus the number of the color, and the foreground with 30
#These are the sequences need to get colored ouput


def formatter_message(record, use_color=False):

    if not use_color:
        return record

    for seq in ALL_COLORS.keys():

        color = ALL_COLORS[seq]
        # search in message
        if isinstance(record, logging.LogRecord):

            record.__dict__[seq.lower()] = color
            if isinstance(record.msg, str):
                find = re.search(f'[$%]{seq.lower()}', record.msg)
                if find:
                    record.msg = record.msg.replace(find.group(0), color)
        elif isinstance(record, str):
            find = re.search(f"[$%]\({seq.lower()}\)s", record)
            if find:
                record = record.replace(find.group(0), color)
    
    if isinstance(record, logging.LogRecord):
        if isinstance(record.msg, str):
            record.msg += f'{ALL_COLORS["RESET"]}'
    else:
        record += f'{ALL_COLORS["RESET"]}'
    return record


# class ColoredPercentStyle(logging.PercentStyle):
#     def format(self, record):
#         try:
#             return self._format(record)
#         except KeyError as e:
#             raise ValueError('Formatting field not found in record: %s' % e)
#
#
# logging._STYLES = {
#     '%': (ColoredPercentStyle, logging.BASIC_FORMAT),
#     '{': (logging.StrFormatStyle, '{levelname}:{name}:{message}'),
#     '$': (logging.StringTemplateStyle, '${levelname}:${name}:${message}'),
# }


class ColoredFormatter(logging.Formatter):

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, use_color=False):
        super(ColoredFormatter, self).__init__(
            fmt=fmt, datefmt=datefmt, style=style, validate=validate
        )
        self.use_color = use_color

    def format(self, record):

        record.message = record.getMessage()
        return super(ColoredFormatter, self).format(
            formatter_message(record, use_color=self.use_color)
        )

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = formatter_message(time.strftime(datefmt, ct), use_color=self.use_color)
        else:
            t = time.strftime(self.default_time_format, ct)
            s = self.default_msec_format % (t, record.msecs)
        return s
