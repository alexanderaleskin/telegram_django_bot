#!/bin/sh

set -e

celery -A src.celery flower --conf=/webapp/flowerconfig.py
