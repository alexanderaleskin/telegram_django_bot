import logging, sys
from telegram.ext import (
    Updater,
)

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_settings')
django.setup()
from django.conf import settings

from telegram_django_bot.routing import RouterCallbackMessageCommandHandler
from telegram_django_bot.tg_dj_bot import TG_DJ_Bot


def add_handlers(updater):
    dp = updater.dispatcher
    dp.add_handler(RouterCallbackMessageCommandHandler())
    # dp.add_handler(MessageHandler(Filters.text, message_written))


def main():
    logging.basicConfig(
        # filename='bot.logs',
        # filemode='a',
        stream=sys.stdout,
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        level=logging.INFO
    )

    updater = Updater(bot=TG_DJ_Bot(settings.TELEGRAM_TOKEN), workers=8)
    add_handlers(updater)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
