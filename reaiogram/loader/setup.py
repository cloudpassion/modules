import os

from config import settings, secrets
from log import logger
from proxyparser import ProxyParser


logger.info(settings)
logger.info(secrets)

pollbot_proxies = [
    ProxyParser(proxy=prx).proxy for prx in secrets.aiogram_pollbot.proxies
]
sendbot_proxies = [
    ProxyParser(proxy=prx).proxy for prx in secrets.aiogram_sendbot.proxies
]

pollbot_proxy = ProxyParser().best_of(pollbot_proxies)
sendbot_proxy = ProxyParser().best_of(pollbot_proxies)

logger.info(f'poll_prx: {pollbot_proxy}\n'
            f'send_prx: {sendbot_proxy}')

API_TOKEN = secrets.aiogram_pollbot.key
API_TOKENS = [API_TOKEN, ]

API_BASE_URL = secrets.aiogram.api_url.base
API_FILE_URL = secrets.aiogram.api_url.file

WEBHOOK = settings.bot.webhook
WEBHOOK_HOST = secrets.aiogram_pollbot.webhook.host
WEBHOOK_PORT = secrets.aiogram_pollbot.webhook.port
WEBHOOK_PATH = secrets.aiogram_pollbot.webhook.path
WEBHOOK_URL = f'{WEBHOOK_HOST}:{WEBHOOK_PORT}/{WEBHOOK_PATH}'
WEBHOOK_SSL = None

WEBAPP_HOST = secrets.aiogram_pollbot.webhook.webapp.host
WEBAPP_PORT = secrets.aiogram_pollbot.webhook.webapp.port
