import logging, sys
from telegram.ext import (
    Updater,
)

import os, django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
django.setup()


from telegram_django_bot.routing import RouterCallbackMessageCommandHandler
from telegram_django_bot.tg_dj_bot import TG_DJ_Bot
# from telega_bot.telega_handlers import ()

from telegram.ext import MessageHandler, Filters
from tests.settings import TELEGRAM_TOKEN
import logging


def add_handlers(updater):
    dp = updater.dispatcher

    # dp.add_handler(CommandHandler("start", start))
    #
    # dp.add_handler(CallbackQueryHandler(goal_info, pattern="^{}".format(GOAL_INFO_BUTTON)))


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

    updater = Updater(bot=TG_DJ_Bot(TELEGRAM_TOKEN), workers=8)
    add_handlers(updater)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()



