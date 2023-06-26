import sys
import select
import asyncio

from reaiogram.default.bot import Bot
from reaiogram.dispatcher import Dispatcher

from config import secrets
from log import logger


async def template(dp: Dispatcher, bot: Bot):

    timeout = 0
    name = __name__.split(".")[-1]
    script = globals().get(name)

    if not timeout:
        return

    logger.info(
        f'{script=} type\n'
        f'\t\t\t\t\t\t" start_await_{name} " await result\n'
        f'\t\t\t\t\t\t" start_task_{name} " create_task',
    )
    i, _, _ = select.select([sys.stdin], [], [], timeout)

    if i:
        run = sys.stdin.readline().strip()
    else:
        run = None

    if run:
        if run == f'start_task_{name}':
            asyncio.create_task(_run_script(script, dp, bot))
        if run == f'start_await_{name}':
            await _run_script(script, dp, bot)


async def _run_script(script, dp: Dispatcher, bot: Bot):
    logger.info(f'{script=} func, {dp=}, {bot=}')
    return
