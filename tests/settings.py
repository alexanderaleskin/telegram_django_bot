import os
import sys
from django.utils.translation import gettext_lazy as _


DIRNAME = os.path.dirname(__file__)

DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "mydatabase"}}

AUTH_USER_MODEL = 'myapp.User'


INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "telegram_django_bot",
    "django_json_widget",
    "tests.myapp",
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

LANGUAGE_CODE = 'ru-RU'
USE_I18N = True

TELEGRAM_TOKEN = '604076170:AAEOy1JQCZ0n-d3LT7DJGjbMaHCla0N4Vag'
TELEGRAM_ROOT_UTRLCONF = 'tests.myapp.utrls'

ROOT_URLCONF = 'tests.urls'

LOCALE_PATHS = [
    os.path.join(DIRNAME, 'locale')
]

LANGUAGES = [
    ('en', _('English')),
    # ('de', _('German')),
    ('ru', _('Russian'))
]



