import asyncio

from log import logger

from .default import default_loader

from .setup import (
    WEBHOOK, WEBHOOK_URL, WEBHOOK_SSL,
)


async def main_loader():

    bots, dp = await default_loader()

    logger.info(f'{bots=}, {dp}')

    if not WEBHOOK:
        await dp.start_polling(
            *bots
        )
    else:
        for bot in bots:
            await bot.set_webhook(
                url=WEBHOOK_URL,
                certificate=WEBHOOK_SSL,
            )
        await dp.start_polling(
            *bots
        )


def run_main():
    asyncio.run(main_loader())
