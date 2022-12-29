import os
import sys
from django.utils.translation import gettext_lazy as _

import environ
env = environ.Env()
environ.Env.read_env()

sys.path.append('..')

DIRNAME = os.path.dirname(__file__)

DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db.sqlite"}}

AUTH_USER_MODEL = 'test_app.User'


INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django_json_widget",
    "telegram_django_bot",
    "test_app",
)

STATIC_URL = "/static/"
SECRET_KEY = "abc123"
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = 'en'
USE_I18N = True


TELEGRAM_TOKEN = env('TELEGRAM_TOKEN')
TELEGRAM_TEST_USER_IDS = list([int(val) for val in env.list('TELEGRAM_TEST_USER_IDS')])
TELEGRAM_ROOT_UTRLCONF = 'test_app.utrls'

ROOT_URLCONF = 'urls'

LOCALE_PATHS = [
    os.path.join(DIRNAME, 'locale')
]

LANGUAGES = [
    ('en', _('English')),
    ('de', _('German')),
    ('ru', _('Russian'))
]



