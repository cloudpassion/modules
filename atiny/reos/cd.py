import os

try:
    from log import logger
except ImportError:
    from ..log import logger


def cd(_file):
    logger.warning(f'{_file=}')
    if '__init__' in _file:
        _file_path = _file.replace(_file.split('/')[-1], '..')
    else:
        _file_path = _file.replace(_file.split('/')[-1], '')

    logger.warning(f'{_file_path=}')

    _absolute_path = os.path.abspath(_file_path)
    logger.warning(f'{_absolute_path=}')

    os.chdir(_absolute_path)

    _script_name = os.path.splitext(_file.split('/')[-1])[0]

    logger.info(f'script_name: {_script_name}, pwd: {os.getcwd()}')
