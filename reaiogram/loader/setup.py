import os
import ssl

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
if WEBHOOK_PORT:
    WEBHOOK_URL = f'{WEBHOOK_HOST}:{WEBHOOK_PORT}/{WEBHOOK_PATH}'
else:
    WEBHOOK_URL = f'{WEBHOOK_HOST}/{WEBHOOK_PATH}'

WEBHOOK_SSL_CERT = secrets.aiogram_pollbot.webhook.ssl.cert
WEBHOOK_SSL_KEY = secrets.aiogram_pollbot.webhook.ssl.key
WEBHOOK_SECRET = secrets.aiogram_pollbot.webhook.secret

if WEBHOOK_SSL_CERT and WEBHOOK_SSL_KEY:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_KEY)

    WEBHOOK_SSL = context
else:
    WEBHOOK_SSL = None

WEBAPP_HOST = secrets.aiogram_pollbot.webhook.webapp.host
WEBAPP_PORT = secrets.aiogram_pollbot.webhook.webapp.port
