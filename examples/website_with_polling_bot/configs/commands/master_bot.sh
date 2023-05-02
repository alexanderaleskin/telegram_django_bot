#!/bin/sh

set -e

sleep 7


python manage.py migrate --noinput

if [ -z ${DJANGO_DEBUG+x} ] || (( "$DJANGO_DEBUG" == "true" ))
then
    nodemon --exec ipython ./run_bot.py
else
    python ./run_bot.py
fi

