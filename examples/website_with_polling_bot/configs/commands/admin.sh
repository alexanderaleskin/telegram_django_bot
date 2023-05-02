#!/bin/sh

set -e

#if [ "$DB_HOST" = "postgres2" ]
#then
#    echo "Waiting for postgres..."
#
#    while ! nc -z $DB_HOST $DB_HOST; do
#      sleep 0.1
#    done
#
#    echo "PostgreSQL started"
#fi

sleep 5

python manage.py migrate --noinput


if [ -z ${DJANGO_DEBUG+x} ] || (( "$DJANGO_DEBUG" == "true" ))
then
    python manage.py runserver 0.0.0.0:80
else
    python manage.py collectstatic --noinput
    uwsgi --ini /configs/uwsgi.ini
fi
