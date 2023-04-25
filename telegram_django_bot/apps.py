from django.apps import AppConfig
# needed for celery auto register
from .tasks import create_triggers, send_triggers


class TelegramDjangoBotConfig(AppConfig):
    name = 'telegram_django_bot'
