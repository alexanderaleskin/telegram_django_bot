#!/bin/sh

set -e
sleep 5

celery -A bot_conf beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=INFO --logfile=/web/logs/celery_beat.log
