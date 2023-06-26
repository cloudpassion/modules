from config import settings
from log import logger
#
# from ....observer.event import EventObserver
#
#
# class SimpleEventObserver(EventObserver):
#     pass


async def simple_startup(*args, **kwargs):
    if settings.tlog.enable and settings.tlog.simple.observer.event:
        logger.info('simple_startup')


async def simple_shutdown(*args, **kwargs):
    if settings.tlog.enable and settings.tlog.simple.observer.event:
        logger.info('simple_shutdown')


def register_simple_event_observer(dp):
    dp.startup.register(simple_startup)
    dp.shutdown.register(simple_shutdown)
