#!/bin/sh

set -e
sleep 5

celery -A bot_conf worker -n main  --concurrency=1 --max-tasks-per-child=100 --max-memory-per-child=25000 --loglevel=INFO --logfile=/web/logs/celery_main.log
