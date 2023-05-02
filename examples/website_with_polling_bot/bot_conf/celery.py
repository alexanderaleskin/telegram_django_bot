"""
IMPORTANT!
To use celery you must install all dependencies from requirements.txt, redis and run celery worker+celery beat+redis.

Example for OSX:
$ brew services start redis
$ celery -A src.main worker -l info
$ celery -A src.main beat -l info -S django
$ python manage.py runserver

Run tasks when system starts:
https://medium.com/@yehandjoe/celery-4-periodic-task-in-django-9f6b5a8c21c7

"""

import os

from celery import Celery
from celery.signals import beat_init
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot_conf.settings')

app = Celery('proj')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

