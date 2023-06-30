import os
import asyncio

from aiohttp import web
from aiogram.webhook.aiohttp_server import (
    setup_application,
    TokenBasedRequestHandler,
    SimpleRequestHandler,
    ip_filter_middleware,
)

from aiogram.types import FSInputFile

from log import logger, log_stack

from .default import default_loader

from .setup import (
    WEBHOOK, WEBHOOK_URL,
    WEBHOOK_SECRET, WEBHOOK_SSL_CERT,
    WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_SSL, WEBHOOK_PATH
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
                log_stack.error('123ch')

            # quit()
            logger.info(f'ex')
            await asyncio.sleep(5)
            bots, dp = await default_loader()

    else:
        for bot in bots:
            logger.info(f'set_webhook: '
                        f'{WEBHOOK_URL=}, '
                        f'{WEBHOOK_SSL=}, '
                        f'{WEBHOOK_SSL_CERT=}')

            # await bot.delete_webhook()
            await bot.set_webhook(
                url=WEBHOOK_URL,
                secret_token=WEBHOOK_SECRET,
                certificate=FSInputFile(path=WEBHOOK_SSL_CERT),
            )

            webhook_info = await bot.get_webhook_info()
            logger.info(f'{webhook_info=}')

            app = web.Application(
                middlewares=[
                    # ip_filter_middleware,
                ]
            )

            app.router.add_route(
                '*',
                path=f'/{WEBHOOK_PATH}',
                handler=SimpleRequestHandler(
                    dispatcher=dp,
                    bot=bot,
                ),
                # name='webhook',
            )

            setup_application(
                app, dp,
                bot=bot, bots=bots,
            )

            await web._run_app(
                app,
                host=WEBAPP_HOST,
                port=WEBAPP_PORT,
                ssl_context=WEBHOOK_SSL,
            )


def run_main():
    # asyncio.run(main_loader(), debug=True)
    asyncio.run(main_loader())

