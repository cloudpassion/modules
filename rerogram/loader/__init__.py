import os
import django

from django.conf import settings as django_settings

from log import log_stack, logger


def setup_django():
    logger.info(f'setup_django')
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        'rerogram.django_telegram.django_telegram.settings'
    )
    os.environ.update(
        {"DJANGO_ALLOW_ASYNC_UNSAFE": "true"}
    )

    django.setup()


if __name__ != "__main__":
    setup_django()
