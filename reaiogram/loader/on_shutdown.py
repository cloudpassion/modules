from log import logger


async def run_on_shutdown(dispatcher, bot, bots, **kwargs):

    logger.info(f'{dispatcher=}, {bot=}, {kwargs=}')

    for _bot in bots:
        await _bot.delete_webhook()
