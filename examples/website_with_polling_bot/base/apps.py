
from django.apps import AppConfig
import asyncio


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
    verbose_name = "Your App data"

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.bot = None
        self.loop = None

    def ready(self):
        import os
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        from threading import Thread
        from telegram.ext import ApplicationBuilder
        from telegram.request import HTTPXRequest
        from telegram_django_bot.tg_dj_bot import TG_DJ_Bot
        from telegram_django_bot.routing import RouterCallbackMessageCommandHandler

        from bot_conf.settings import TELEGRAM_TOKEN

        proxy_url = 'http://127.0.0.1:3128'
        request1 = HTTPXRequest(proxy_url=proxy_url)
        request2 = HTTPXRequest(proxy_url=proxy_url)
        bot = TG_DJ_Bot(TELEGRAM_TOKEN, request=request1, get_updates_request=request2)
        bot = TG_DJ_Bot(TELEGRAM_TOKEN)
        self.bot = bot
        application = ApplicationBuilder().bot(bot).build()
        application.add_handler(RouterCallbackMessageCommandHandler())

        self.loop = loop = asyncio.get_event_loop()
        t = Thread(target=start_telegram, args=(loop, application), daemon=True)
        t.start()


def start_telegram(loop, application):
    asyncio.set_event_loop(loop)
    print('Telegram load')
    try:
        loop.run_until_complete(application.initialize())
        if application.post_init:
            loop.run_until_complete(application.post_init(application))
        loop.run_until_complete(application.updater.start_polling())  # one of updater.start_webhook/polling
        loop.run_until_complete(application.start())
        loop.run_forever()
    except Exception as e:
        print(e)
