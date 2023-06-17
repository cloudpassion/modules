import os
import django

from config import settings, secrets
from log import logger
from reaiogram.proxyparser import ProxyParser


logger.info(settings)
logger.info(secrets)

pollbot_proxies = [ProxyParser(proxy=prx).proxy for prx in secrets.aiogram_pollbot.proxies]
sendbot_proxies = [ProxyParser(proxy=prx).proxy for prx in secrets.aiogram_sendbot.proxies]

pollbot_proxy = ProxyParser().best_of(pollbot_proxies)
sendbot_proxy = ProxyParser().best_of(pollbot_proxies)

logger.info(f'poll_prx: {pollbot_proxy}\n'
            f'send_prx: {sendbot_proxy}')

API_TOKEN = secrets.aiogram_pollbot.key
API_URL = settings.aiogram.API_URL

WEBHOOK = settings.bot.webhook
WEBHOOK_HOST = secrets.aiogram_pollbot.webhook.host
WEBHOOK_PORT = secrets.aiogram_pollbot.webhook.port
WEBHOOK_PATH = secrets.aiogram_pollbot.webhook.path
WEBHOOK_URL = f'{WEBHOOK_HOST}:{WEBHOOK_PORT}/{WEBHOOK_PATH}'

WEBAPP_HOST = secrets.aiogram_pollbot.webhook.webapp.host
WEBAPP_PORT = secrets.aiogram_pollbot.webhook.webapp.port


def register_middlewares(dp):
    from reaiogram.middlewares import register_middlewares
    register_middlewares(dp)


def register_dialogs(dp):
    return
    #from ..dialogs import register_dialogs


def register_filters(dp):
    from reaiogram.filters import register_filters
    register_filters(dp)


def register_handlers(dp):
    return
    #from ..handlers import register_handlers
    #register_handlers(dp)


def register_webhook(bot):
    if WEBHOOK:
        bot.set_webhook(
            url=WEBHOOK_URL,
            certificate=SSL_CERTIFICATE
        )


def setup_django():
    logger.info(f'setup_django')
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "reaiogram.django_telegram.django_telegram.settings"
    )
    os.environ.update(
        {"DJANGO_ALLOW_ASYNC_UNSAFE": "true"}
    )
    django.setup()


if __name__ != "__main__":
    setup_django()
