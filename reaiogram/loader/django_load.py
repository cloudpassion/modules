import os
import django

from log import logger


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
