import asyncio

from log import logger, log_stack

from .default import default_loader

from .setup import (
    WEBHOOK, WEBHOOK_URL, WEBHOOK_SSL,
)


async def main_loader():

    bots, dp = await default_loader()

    logger.info(f'{bots=}, {dp}')

    if not WEBHOOK:
        while True:
            try:

                await dp.start_polling(
                    *bots,
                    # close_bot_session=False,
                    # polling_timeout=60,
                )
            except Exception as exc:
                log_stack.error('ch')

            quit()
            logger.info(f'ex')
            await asyncio.sleep(5)
            bots, dp = await default_loader()

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
